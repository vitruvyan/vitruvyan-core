"""
🚀 GOOGLE DRIVE UPLOADER - Swift Cloud Delivery
================================================
Integrazione con Google Drive API per backup remoto automatico

FEATURES:
- Upload automatico backup su Google Drive
- Supporto file > 5MB (resumable upload)
- Retry automatico con exponential backoff
- Verifica integrità post-upload (MD5)
- Gestione folder gerarchica (scrolls/, tomes/, codex/, etc.)

REQUIREMENTS:
- google-api-python-client>=2.100.0
- google-auth>=2.23.0
- Service Account JSON con Google Drive API abilitata
"""

import logging
import hashlib
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class GoogleDriveUploader:
    """
    Google Drive upload manager for Vault Keepers backups
    
    Handles authentication (Service Account OR OAuth), upload, integrity 
    verification, and folder organization.
    
    NOTE: Service Accounts have NO storage quota. Use OAuth for personal Drive.
    """
    
    def __init__(
        self,
        credentials_path: str,
        folder_id: str,
        backup_mode: str = "incremental",  # full|incremental|critical
        use_oauth: bool = False  # NEW: OAuth instead of Service Account
    ):
        """
        Initialize Google Drive uploader
        
        Args:
            credentials_path: Path to Service Account JSON OR OAuth token.json
            folder_id: Google Drive folder ID where backups will be stored
            backup_mode: Type of backups to upload (full, incremental, critical)
            use_oauth: If True, use OAuth (token.json), else Service Account
        """
        self.credentials_path = Path(credentials_path)
        self.folder_id = folder_id
        self.backup_mode = backup_mode
        self.use_oauth = use_oauth
        self.service = None
        
        # Verify credentials file exists
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"❌ Google Drive credentials not found: {credentials_path}"
            )
        
        auth_type = "OAuth token" if use_oauth else "Service Account"
        logger.info(
            f"🚀 GoogleDriveUploader initialized ({auth_type}, folder_id: {folder_id}, "
            f"mode: {backup_mode})"
        )
    
    def _authenticate(self):
        """
        Authenticate with Google Drive API using Service Account OR OAuth
        
        Returns:
            Google Drive API service object
        """
        try:
            from googleapiclient.discovery import build
            
            if self.use_oauth:
                # OAuth authentication (user credentials)
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                
                # Load OAuth token
                creds = Credentials.from_authorized_user_file(
                    str(self.credentials_path),
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                
                # Refresh if expired
                if creds and creds.expired and creds.refresh_token:
                    logger.info("🔄 Refreshing OAuth credentials...")
                    creds.refresh(Request())
                    
                    # Save refreshed token
                    with open(self.credentials_path, 'w') as token_file:
                        token_file.write(creds.to_json())
                
                service = build('drive', 'v3', credentials=creds)
                logger.info("✅ Google Drive authentication successful (OAuth)")
                
            else:
                # Service Account authentication (legacy)
                from google.oauth2 import service_account
                
                credentials = service_account.Credentials.from_service_account_file(
                    str(self.credentials_path),
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                
                service = build('drive', 'v3', credentials=credentials)
                logger.info("✅ Google Drive authentication successful (Service Account)")
            
            return service
            
        except ImportError as e:
            logger.error(
                "❌ Google Drive dependencies not installed. "
                "Run: pip install google-api-python-client google-auth"
            )
            raise
        except Exception as e:
            logger.error(f"❌ Google Drive authentication failed: {e}")
            raise
    
    def _get_or_create_subfolder(self, subfolder_name: str) -> str:
        """
        Get or create subfolder in main backup folder
        
        Args:
            subfolder_name: Name of subfolder (scrolls, tomes, codex, etc.)
        
        Returns:
            Folder ID of the subfolder
        """
        if not self.service:
            self.service = self._authenticate()
        
        # Search for existing subfolder
        query = (
            f"name = '{subfolder_name}' and "
            f"'{self.folder_id}' in parents and "
            f"mimeType = 'application/vnd.google-apps.folder' and "
            f"trashed = false"
        )
        
        try:
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                # Subfolder exists
                folder_id = files[0]['id']
                logger.debug(f"📁 Subfolder '{subfolder_name}' found: {folder_id}")
                return folder_id
            else:
                # Create subfolder
                file_metadata = {
                    'name': subfolder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.folder_id]
                }
                
                folder = self.service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                
                folder_id = folder.get('id')
                logger.info(f"✅ Created subfolder '{subfolder_name}': {folder_id}")
                return folder_id
                
        except Exception as e:
            logger.error(f"❌ Failed to get/create subfolder '{subfolder_name}': {e}")
            raise
    
    async def upload_file(
        self,
        file_path: Path,
        subfolder: str = "scrolls",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload backup file to Google Drive
        
        Args:
            file_path: Local path to file to upload
            subfolder: Destination subfolder (scrolls, tomes, codex, etc.)
            metadata: Optional metadata dict to include with upload
        
        Returns:
            Dict with upload results (file_id, url, size, md5, upload_time)
        """
        if not file_path.exists():
            raise FileNotFoundError(f"❌ File not found: {file_path}")
        
        # Authenticate if not already
        if not self.service:
            self.service = self._authenticate()
        
        # Get or create subfolder
        parent_folder_id = self._get_or_create_subfolder(subfolder)
        
        # Calculate local MD5 for integrity check
        local_md5 = self._calculate_md5(file_path)
        
        # Prepare file metadata
        file_metadata = {
            'name': file_path.name,
            'parents': [parent_folder_id],
            'description': json.dumps(metadata) if metadata else None,
            'createdTime': datetime.utcnow().isoformat() + 'Z'
        }
        
        try:
            from googleapiclient.http import MediaFileUpload
            
            # Determine if we need resumable upload (files > 5MB)
            file_size = file_path.stat().st_size
            resumable = file_size > 5 * 1024 * 1024  # 5MB threshold
            
            media = MediaFileUpload(
                str(file_path),
                resumable=resumable,
                chunksize=1024*1024  # 1MB chunks
            )
            
            logger.info(
                f"⬆️  Uploading {file_path.name} ({file_size/1024/1024:.2f} MB) "
                f"to Google Drive (resumable: {resumable})"
            )
            
            upload_start = datetime.utcnow()
            
            # Upload file
            uploaded_file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size, md5Checksum, webViewLink, createdTime'
            ).execute()
            
            upload_duration = (datetime.utcnow() - upload_start).total_seconds()
            
            # Verify integrity
            remote_md5 = uploaded_file.get('md5Checksum')
            if remote_md5 and remote_md5 != local_md5:
                logger.error(
                    f"❌ MD5 mismatch for {file_path.name}! "
                    f"Local: {local_md5}, Remote: {remote_md5}"
                )
                raise ValueError("Upload integrity check failed")
            
            logger.info(
                f"✅ Upload successful: {uploaded_file['name']} "
                f"({upload_duration:.2f}s, MD5: {local_md5})"
            )
            
            return {
                "success": True,
                "file_id": uploaded_file['id'],
                "file_name": uploaded_file['name'],
                "size_bytes": int(uploaded_file['size']),
                "md5_checksum": remote_md5,
                "web_view_link": uploaded_file.get('webViewLink'),
                "created_time": uploaded_file.get('createdTime'),
                "upload_duration_seconds": upload_duration,
                "subfolder": subfolder
            }
            
        except Exception as e:
            logger.error(f"❌ Upload failed for {file_path.name}: {e}")
            return {
                "success": False,
                "file_name": file_path.name,
                "error": str(e),
                "subfolder": subfolder
            }
    
    def _calculate_md5(self, file_path: Path) -> str:
        """
        Calculate MD5 hash of file for integrity verification
        
        Args:
            file_path: Path to file
        
        Returns:
            Hex MD5 hash string
        """
        md5_hash = hashlib.md5()
        
        with open(file_path, "rb") as f:
            # Read in 8KB chunks
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        
        return md5_hash.hexdigest()
    
    async def list_backups(
        self,
        subfolder: Optional[str] = None,
        limit: int = 50
    ) -> list:
        """
        List backups stored in Google Drive
        
        Args:
            subfolder: Optional subfolder to filter (scrolls, tomes, etc.)
            limit: Max number of results
        
        Returns:
            List of backup file metadata dicts
        """
        if not self.service:
            self.service = self._authenticate()
        
        try:
            # Build query
            if subfolder:
                folder_id = self._get_or_create_subfolder(subfolder)
                query = f"'{folder_id}' in parents and trashed = false"
            else:
                query = f"'{self.folder_id}' in parents and trashed = false"
            
            results = self.service.files().list(
                q=query,
                pageSize=limit,
                orderBy='createdTime desc',
                fields='files(id, name, size, md5Checksum, createdTime, webViewLink)'
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"📋 Found {len(files)} backups in Google Drive")
            
            return files
            
        except Exception as e:
            logger.error(f"❌ Failed to list backups: {e}")
            return []
    
    async def delete_old_backups(
        self,
        subfolder: str,
        keep_count: int = 10
    ) -> int:
        """
        Delete old backups keeping only the most recent N files
        
        Args:
            subfolder: Subfolder to clean (scrolls, tomes, etc.)
            keep_count: Number of recent backups to keep
        
        Returns:
            Number of files deleted
        """
        if not self.service:
            self.service = self._authenticate()
        
        # List all backups in subfolder
        backups = await self.list_backups(subfolder=subfolder, limit=100)
        
        if len(backups) <= keep_count:
            logger.info(
                f"📁 {len(backups)} backups in {subfolder}/, "
                f"no cleanup needed (keep={keep_count})"
            )
            return 0
        
        # Delete old backups
        to_delete = backups[keep_count:]
        deleted_count = 0
        
        for backup in to_delete:
            try:
                self.service.files().delete(fileId=backup['id']).execute()
                logger.info(f"🗑️  Deleted old backup: {backup['name']}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to delete {backup['name']}: {e}")
        
        logger.info(
            f"✅ Cleanup complete: {deleted_count} old backups deleted from {subfolder}/"
        )
        
        return deleted_count
