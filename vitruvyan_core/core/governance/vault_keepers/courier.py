"""
🚀 THE COURIER - Nuntius Velox
==============================
The Swift Messenger of the Vault

Like the riders of the Pony Express galloping across vast frontiers,
The Courier ensures critical backups reach distant sanctuaries swiftly,
carrying precious cargo across digital realms to secure remote vaults.

RESPONSIBILITIES:
- Distribute backup archives to remote locations
- Manage secure transfer protocols and encryption
- Verify successful delivery and remote integrity
- Coordinate with external backup services (AWS S3, Google Cloud, etc.)
- Handle emergency evacuation of critical data

SWIFT DOMAINS:
- Remote cloud storage (S3, GCS, Azure Blob)
- Secure FTP/SFTP transfer protocols
- Encrypted peer-to-peer vault networks
- Emergency evacuation channels
- Multi-region redundancy coordination

MOTTO: "Celeritas et securitas" (Speed and security)
"""

import asyncio
import logging
import shutil
import hashlib
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import json
import base64
import gzip
from dataclasses import dataclass
import os

from .keeper import BaseKeeper, VaultEvent, BackupMode, VaultStatus, VaultConfig
from .gdrive_uploader import GoogleDriveUploader

logger = logging.getLogger(__name__)

@dataclass
class DeliveryChannel:
    """Configuration for a backup delivery channel"""
    name: str
    type: str  # 's3', 'gcs', 'sftp', 'local', 'webhook'
    config: Dict[str, Any]
    priority: int = 1
    enabled: bool = True
    encryption_required: bool = True
    max_file_size_mb: int = 1000

@dataclass
class DeliveryJob:
    """Represents a delivery job for the Courier"""
    job_id: str
    backup_id: str
    artifacts: List[Dict[str, Any]]
    channels: List[DeliveryChannel]
    priority: int = 1
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, in_progress, completed, failed, cancelled
    delivery_results: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.delivery_results is None:
            self.delivery_results = []

class CourierAgent(BaseKeeper):
    """
    The Courier - Nuntius Velox
    
    The fleet-footed messenger of the fortress, who carries vital scrolls
    and treasures across vast distances to ensure they survive even if
    the original fortress falls to siege.
    
    Like Hermes with his winged sandals, The Courier moves with divine
    speed, ensuring no precious data is ever truly lost.
    """
    
    def __init__(self, config: Optional[VaultConfig] = None):
        super().__init__(config)
        
        # Courier Configuration
        self.delivery_channels: List[DeliveryChannel] = []
        self.active_jobs: Dict[str, DeliveryJob] = {}
        self.job_queue: asyncio.Queue = asyncio.Queue()
        
        # Delivery Statistics
        self.total_deliveries = 0
        self.total_bytes_delivered = 0
        self.failed_deliveries = 0
        self.average_delivery_time = 0.0
        
        # Encryption settings
        self.encryption_key = self._get_encryption_key()
        
        # Initialize default delivery channels
        self._initialize_delivery_channels()
        
        # Start delivery worker
        self.delivery_worker_task = None
        
        self.logger.info("🚀 The Courier readies for swift delivery - saddlebags packed, routes planned")
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key for secure deliveries"""
        # In practice, this would use proper key management
        # Use postgres password as base for encryption key generation
        vault_secret = getattr(self.config, 'vault_secret_key', self.config.postgres_password)
        key_source = f"{vault_secret}:courier_encryption"
        return hashlib.sha256(key_source.encode()).digest()
    
    def _initialize_delivery_channels(self):
        """Initialize default delivery channels based on configuration"""
        
        # Local filesystem backup channel (always available)
        local_channel = DeliveryChannel(
            name="local_redundant",
            type="local",
            config={
                "base_path": "/var/backup/vitruvyan_redundant",
                "max_retention_days": 90
            },
            priority=3,
            encryption_required=False  # Local filesystem, encryption optional
        )
        self.delivery_channels.append(local_channel)
        
        # AWS S3 channel (if configured)
        if hasattr(self.config, 'aws_access_key') and self.config.aws_access_key:
            s3_channel = DeliveryChannel(
                name="aws_s3_primary",
                type="s3",
                config={
                    "bucket": getattr(self.config, 'aws_s3_bucket', 'vitruvyan-backups'),
                    "region": getattr(self.config, 'aws_region', 'us-east-1'),
                    "access_key": self.config.aws_access_key,
                    "secret_key": getattr(self.config, 'aws_secret_key', ''),
                    "prefix": "vault_backups/"
                },
                priority=1,
                max_file_size_mb=5000  # S3 handles large files well
            )
            self.delivery_channels.append(s3_channel)
        
        # Google Drive Storage channel (if configured)
        gdrive_enabled = os.getenv('GDRIVE_ENABLED', 'false').lower() == 'true'
        if gdrive_enabled:
            # Determine if using OAuth or Service Account
            use_oauth = self.config.gdrive_use_oauth if hasattr(self.config, 'gdrive_use_oauth') else True
            
            # Select credentials path based on auth method
            if use_oauth:
                creds_path = self.config.gdrive_token_path if hasattr(self.config, 'gdrive_token_path') else "/app/secrets/token.json"
            else:
                creds_path = self.config.gdrive_service_account_path if hasattr(self.config, 'gdrive_service_account_path') else os.getenv('GDRIVE_SERVICE_ACCOUNT_PATH')
            
            gdrive_channel = DeliveryChannel(
                name="gdrive_primary",
                type="gdrive",
                config={
                    "folder_id": os.getenv('GDRIVE_FOLDER_ID'),
                    "use_oauth": use_oauth,
                    "oauth_token_path": creds_path if use_oauth else None,
                    "service_account_path": creds_path if not use_oauth else None,
                    "backup_mode": os.getenv('GDRIVE_BACKUP_MODE', 'incremental'),
                    "auto_delete_local": os.getenv('GDRIVE_AUTO_DELETE_LOCAL', 'true').lower() == 'true',
                    "keep_count": int(os.getenv('GDRIVE_KEEP_COUNT', '30'))
                },
                priority=1,  # Highest priority
                max_file_size_mb=5000  # Google Drive handles large files well
            )
            self.delivery_channels.append(gdrive_channel)
            auth_method = "OAuth" if use_oauth else "Service Account"
            self.logger.info(f"📁 Google Drive delivery channel enabled ({auth_method}, folder: {gdrive_channel.config['folder_id']})")
        
        # Emergency webhook channel (for critical alerts)
        if hasattr(self.config, 'emergency_webhook_url') and self.config.emergency_webhook_url:
            webhook_channel = DeliveryChannel(
                name="emergency_webhook",
                type="webhook",
                config={
                    "url": self.config.emergency_webhook_url,
                    "auth_header": getattr(self.config, 'webhook_auth_header', ''),
                    "max_payload_mb": 50  # Webhooks should be lightweight
                },
                priority=0,  # Highest priority for emergencies
                max_file_size_mb=50
            )
            self.delivery_channels.append(webhook_channel)
        
        self.logger.info(f"📫 The Courier established {len(self.delivery_channels)} delivery routes")
    
    async def start_delivery_service(self):
        """Start the courier delivery service"""
        if self.delivery_worker_task:
            self.logger.warning("⚠️ Courier delivery service already running")
            return
        
        self.delivery_worker_task = asyncio.create_task(self._delivery_worker())
        self.logger.info("🏃 The Courier begins delivery rounds - service active")
        
        self.publish_event("courier.service_started", {
            "channels_available": len(self.delivery_channels),
            "channels_enabled": len([c for c in self.delivery_channels if c.enabled])
        })
    
    async def stop_delivery_service(self):
        """Stop the courier delivery service gracefully"""
        if self.delivery_worker_task:
            self.delivery_worker_task.cancel()
            try:
                await self.delivery_worker_task
            except asyncio.CancelledError:
                pass
            self.delivery_worker_task = None
        
        self.logger.info("🛑 The Courier ends delivery rounds - service stopped")
        self.publish_event("courier.service_stopped", {})
    
    async def dispatch_backup(self, backup_result: Dict[str, Any], delivery_priority: int = 1) -> str:
        """
        Dispatch backup artifacts for delivery to remote locations
        
        Like sending urgent messages via multiple riders to ensure
        at least one reaches its destination safely.
        """
        backup_id = backup_result.get("backup_id", "unknown")
        backup_type = backup_result.get("type", "unknown")
        artifacts = backup_result.get("artifacts", [])
        
        if not artifacts:
            self.logger.warning(f"⚠️ No artifacts to deliver for backup {backup_id}")
            return None
        
        # Create delivery job
        job_id = f"delivery_{backup_id}_{int(datetime.utcnow().timestamp())}"
        
        # Select appropriate channels based on backup type and priority
        selected_channels = self._select_delivery_channels(backup_type, delivery_priority)
        
        delivery_job = DeliveryJob(
            job_id=job_id,
            backup_id=backup_id,
            artifacts=artifacts,
            channels=selected_channels,
            priority=delivery_priority
        )
        
        self.active_jobs[job_id] = delivery_job
        
        # Add to delivery queue
        await self.job_queue.put(delivery_job)
        
        self.logger.info(f"📦 The Courier dispatched delivery job {job_id} for backup {backup_id}")
        self.logger.info(f"📋 Delivery manifest: {len(artifacts)} artifacts via {len(selected_channels)} channels")
        
        self.publish_event("courier.job_dispatched", {
            "job_id": job_id,
            "backup_id": backup_id,
            "backup_type": backup_type,
            "artifacts_count": len(artifacts),
            "delivery_channels": [c.name for c in selected_channels],
            "priority": delivery_priority
        })
        
        return job_id
    
    def _select_delivery_channels(self, backup_type: str, priority: int) -> List[DeliveryChannel]:
        """Select appropriate delivery channels based on backup characteristics"""
        
        # Filter enabled channels
        available_channels = [c for c in self.delivery_channels if c.enabled]
        
        if backup_type == "disaster_recovery":
            # Emergency: use all available channels for maximum redundancy
            selected = available_channels
            
        elif backup_type == "critical":
            # Critical: use high-priority channels (priority 0-2)
            selected = [c for c in available_channels if c.priority <= 2]
            
        elif backup_type == "full_system":
            # Full backup: use primary and secondary channels
            selected = [c for c in available_channels if c.priority <= 3]
            
        else:
            # Incremental: use most efficient channels
            selected = [c for c in available_channels if c.priority <= 2][:2]  # Limit to 2 channels
        
        # Ensure we have at least one channel
        if not selected and available_channels:
            selected = [available_channels[0]]  # Use first available as fallback
        
        # Sort by priority (lower number = higher priority)
        selected.sort(key=lambda c: c.priority)
        
        return selected
    
    async def _delivery_worker(self):
        """Main delivery worker loop"""
        while True:
            try:
                # Get next delivery job
                delivery_job = await self.job_queue.get()
                
                self.logger.info(f"🚀 The Courier begins delivery mission: {delivery_job.job_id}")
                
                # Update job status
                delivery_job.status = "in_progress"
                
                # Execute deliveries
                success = await self._execute_delivery_job(delivery_job)
                
                # Update job completion
                delivery_job.completed_at = datetime.utcnow()
                delivery_job.status = "completed" if success else "failed"
                
                # Update statistics
                self._update_delivery_statistics(delivery_job)
                
                # Cleanup completed job after some time
                asyncio.create_task(self._cleanup_job(delivery_job.job_id, delay_minutes=30))
                
                self.job_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Courier delivery worker error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _execute_delivery_job(self, job: DeliveryJob) -> bool:
        """Execute delivery job across all configured channels"""
        
        total_success = False
        
        # Process each artifact
        for artifact in job.artifacts:
            artifact_path = Path(artifact.get("path", ""))
            
            if not artifact_path.exists():
                self.logger.warning(f"⚠️ Artifact not found: {artifact_path}")
                continue
            
            # Attempt delivery to each channel
            for channel in job.channels:
                try:
                    delivery_result = await self._deliver_to_channel(artifact, channel, job)
                    job.delivery_results.append(delivery_result)
                    
                    if delivery_result["status"] == "success":
                        total_success = True
                        self.logger.info(f"✅ Successful delivery via {channel.name}: {artifact['type']}")
                    else:
                        self.logger.warning(f"⚠️ Failed delivery via {channel.name}: {delivery_result['error']}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Delivery error to {channel.name}: {e}")
                    job.delivery_results.append({
                        "channel": channel.name,
                        "artifact": artifact.get("type", "unknown"),
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        # Record delivery job results
        await self._record_delivery_job(job, total_success)
        
        return total_success
    
    async def _deliver_to_channel(self, artifact: Dict[str, Any], channel: DeliveryChannel, job: DeliveryJob) -> Dict[str, Any]:
        """Deliver single artifact to a specific channel"""
        
        artifact_path = Path(artifact["path"])
        artifact_size = artifact.get("size_bytes", artifact_path.stat().st_size)
        
        # Check size limits
        if artifact_size > (channel.max_file_size_mb * 1024 * 1024):
            return {
                "channel": channel.name,
                "artifact": artifact.get("type", "unknown"),
                "status": "skipped", 
                "error": f"File too large: {artifact_size / (1024*1024):.1f}MB > {channel.max_file_size_mb}MB",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Encrypt artifact if required
        delivery_path = artifact_path
        if channel.encryption_required:
            encrypted_path = await self._encrypt_artifact(artifact_path, job.job_id)
            if encrypted_path:
                delivery_path = encrypted_path
            else:
                return {
                    "channel": channel.name,
                    "artifact": artifact.get("type", "unknown"),
                    "status": "failed",
                    "error": "Encryption failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # Dispatch to appropriate handler
        if channel.type == "local":
            result = await self._deliver_local(delivery_path, artifact, channel, job)
        elif channel.type == "s3":
            result = await self._deliver_s3(delivery_path, artifact, channel, job)
        elif channel.type == "gcs":
            result = await self._deliver_gcs(delivery_path, artifact, channel, job)
        elif channel.type == "gdrive":
            result = await self._deliver_gdrive(delivery_path, artifact, channel, job)
        elif channel.type == "webhook":
            result = await self._deliver_webhook(delivery_path, artifact, channel, job)
        else:
            result = {
                "channel": channel.name,
                "artifact": artifact.get("type", "unknown"),
                "status": "failed",
                "error": f"Unknown channel type: {channel.type}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Cleanup encrypted temp file
        if channel.encryption_required and delivery_path != artifact_path:
            try:
                delivery_path.unlink()
            except:
                pass
        
        return result
    
    async def _encrypt_artifact(self, artifact_path: Path, job_id: str) -> Optional[Path]:
        """Encrypt artifact for secure delivery"""
        try:
            # Create temporary encrypted file
            temp_dir = Path(tempfile.gettempdir())
            encrypted_path = temp_dir / f"{job_id}_{artifact_path.name}.encrypted"
            
            # Simple XOR encryption (in practice, use proper AES encryption)
            with open(artifact_path, 'rb') as infile, open(encrypted_path, 'wb') as outfile:
                # Write encryption header
                header = {
                    "encrypted": True,
                    "algorithm": "xor_simple",
                    "original_name": artifact_path.name,
                    "encrypted_at": datetime.utcnow().isoformat()
                }
                header_bytes = json.dumps(header).encode()
                outfile.write(len(header_bytes).to_bytes(4, 'big'))
                outfile.write(header_bytes)
                
                # Encrypt data (simple XOR for demo - use AES in production)
                key_cycle = 0
                while True:
                    chunk = infile.read(8192)
                    if not chunk:
                        break
                    
                    encrypted_chunk = bytearray()
                    for byte in chunk:
                        encrypted_chunk.append(byte ^ self.encryption_key[key_cycle % len(self.encryption_key)])
                        key_cycle += 1
                    
                    outfile.write(encrypted_chunk)
            
            return encrypted_path
            
        except Exception as e:
            self.logger.error(f"❌ Encryption failed for {artifact_path}: {e}")
            return None
    
    async def _deliver_local(self, artifact_path: Path, artifact: Dict[str, Any], channel: DeliveryChannel, job: DeliveryJob) -> Dict[str, Any]:
        """Deliver to local filesystem"""
        try:
            base_path = Path(channel.config["base_path"])
            base_path.mkdir(parents=True, exist_ok=True)
            
            # Create backup-specific directory
            backup_dir = base_path / job.backup_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy artifact
            destination = backup_dir / artifact_path.name
            shutil.copy2(artifact_path, destination)
            
            # Verify copy integrity
            original_hash = self.calculate_file_hash(str(artifact_path))
            copied_hash = self.calculate_file_hash(str(destination))
            
            if original_hash != copied_hash:
                return {
                    "channel": channel.name,
                    "artifact": artifact.get("type", "unknown"),
                    "status": "failed",
                    "error": "Integrity check failed after copy",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return {
                "channel": channel.name,
                "artifact": artifact.get("type", "unknown"),
                "status": "success",
                "destination": str(destination),
                "size_bytes": destination.stat().st_size,
                "integrity_hash": copied_hash,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "channel": channel.name,
                "artifact": artifact.get("type", "unknown"),
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _deliver_s3(self, artifact_path: Path, artifact: Dict[str, Any], channel: DeliveryChannel, job: DeliveryJob) -> Dict[str, Any]:
        """Deliver to AWS S3"""
        try:
            # In production, use boto3 for S3 uploads
            # This is a simplified mock implementation
            
            bucket = channel.config["bucket"]
            prefix = channel.config.get("prefix", "")
            s3_key = f"{prefix}{job.backup_id}/{artifact_path.name}"
            
            # Mock S3 upload (in real implementation, use boto3)
            upload_successful = True  # Simulate successful upload
            
            if upload_successful:
                return {
                    "channel": channel.name,
                    "artifact": artifact.get("type", "unknown"),
                    "status": "success",
                    "destination": f"s3://{bucket}/{s3_key}",
                    "size_bytes": artifact_path.stat().st_size,
                    "s3_etag": "mock_etag_hash",  # Would be real ETag from S3
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "channel": channel.name,
                    "artifact": artifact.get("type", "unknown"),
                    "status": "failed",
                    "error": "S3 upload failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "channel": channel.name,
                "artifact": artifact.get("type", "unknown"),
                "status": "failed",
                "error": f"S3 delivery error: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _deliver_gcs(self, artifact_path: Path, artifact: Dict[str, Any], channel: DeliveryChannel, job: DeliveryJob) -> Dict[str, Any]:
        """Deliver to Google Cloud Storage"""
        try:
            # In production, use google-cloud-storage library
            # This is a simplified mock implementation
            
            bucket = channel.config["bucket"]
            prefix = channel.config.get("prefix", "")
            blob_name = f"{prefix}{job.backup_id}/{artifact_path.name}"
            
            # Mock GCS upload
            upload_successful = True  # Simulate successful upload
            
            if upload_successful:
                return {
                    "channel": channel.name,
                    "artifact": artifact.get("type", "unknown"),
                    "status": "success",
                    "destination": f"gs://{bucket}/{blob_name}",
                    "size_bytes": artifact_path.stat().st_size,
                    "gcs_etag": "mock_gcs_etag",  # Would be real etag from GCS
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "channel": channel.name,
                    "artifact": artifact.get("type", "unknown"),
                    "status": "failed",
                    "error": "GCS upload failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "channel": channel.name,
                "artifact": artifact.get("type", "unknown"),
                "status": "failed",
                "error": f"GCS delivery error: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _deliver_gdrive(self, artifact_path: Path, artifact: Dict[str, Any], channel: DeliveryChannel, job: DeliveryJob) -> Dict[str, Any]:
        """Deliver backup file to Google Drive"""
        try:
            # Check if using OAuth or Service Account
            use_oauth = channel.config.get("use_oauth", False)
            creds_key = "oauth_token_path" if use_oauth else "service_account_path"
            creds_path = channel.config.get(creds_key)
            
            if not creds_path:
                # Fallback to old key name for backward compatibility
                creds_path = channel.config.get("service_account_path")
            
            # Initialize Google Drive uploader
            uploader = GoogleDriveUploader(
                credentials_path=creds_path,
                folder_id=channel.config["folder_id"],
                backup_mode=channel.config.get("backup_mode", "incremental"),
                use_oauth=use_oauth
            )
            
            # Determine subfolder based on artifact type
            artifact_type = artifact.get("type", "scrolls")
            subfolder_map = {
                "database": "scrolls",
                "vector": "codex",
                "config": "tomes",
                "logs": "chronicles",
                "state": "relics"
            }
            subfolder = subfolder_map.get(artifact_type, "scrolls")
            
            # Upload file to Google Drive
            upload_result = await uploader.upload_file(
                file_path=artifact_path,
                subfolder=subfolder,
                metadata={
                    "backup_id": job.backup_id,
                    "job_id": job.job_id,
                    "artifact_type": artifact_type,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            if upload_result.get("success"):
                self.logger.info(
                    f"✅ Google Drive upload successful: {artifact_path.name} → {subfolder}/ "
                    f"(file_id: {upload_result['file_id']}, size: {upload_result['size_bytes']/1024/1024:.2f}MB)"
                )
                
                # Auto-delete local file if configured
                if channel.config.get("auto_delete_local", True):
                    try:
                        artifact_path.unlink()
                        self.logger.info(f"🗑️  Local file deleted: {artifact_path.name}")
                    except Exception as e:
                        self.logger.warning(f"⚠️  Failed to delete local file {artifact_path.name}: {e}")
                
                # Cleanup old backups on Google Drive
                keep_count = channel.config.get("keep_count", 30)
                if keep_count > 0:
                    deleted_count = await uploader.delete_old_backups(subfolder, keep_count)
                    if deleted_count > 0:
                        self.logger.info(f"🧹 Cleaned up {deleted_count} old backups from {subfolder}/")
                
                return {
                    "channel": channel.name,
                    "artifact": artifact.get("type", "unknown"),
                    "status": "delivered",
                    "destination": f"gdrive://{channel.config['folder_id']}/{subfolder}/",
                    "file_id": upload_result["file_id"],
                    "web_view_link": upload_result.get("web_view_link"),
                    "size_bytes": upload_result["size_bytes"],
                    "md5_checksum": upload_result.get("md5_checksum"),
                    "upload_duration_seconds": upload_result.get("upload_duration_seconds"),
                    "local_deleted": channel.config.get("auto_delete_local", True),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "channel": channel.name,
                    "artifact": artifact.get("type", "unknown"),
                    "status": "failed",
                    "error": upload_result.get("error", "Unknown upload error"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ Google Drive delivery error: {e}")
            return {
                "channel": channel.name,
                "artifact": artifact.get("type", "unknown"),
                "status": "failed",
                "error": f"Google Drive delivery error: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _deliver_webhook(self, artifact_path: Path, artifact: Dict[str, Any], channel: DeliveryChannel, job: DeliveryJob) -> Dict[str, Any]:
        """Deliver via webhook (for notifications and small payloads)"""
        try:
            webhook_url = channel.config["url"]
            auth_header = channel.config.get("auth_header", "")
            max_size_mb = channel.config.get("max_payload_mb", 10)
            
            # Check if file is small enough for webhook
            file_size_mb = artifact_path.stat().st_size / (1024 * 1024)
            
            if file_size_mb > max_size_mb:
                # Send metadata only for large files
                payload = {
                    "type": "backup_notification",
                    "job_id": job.job_id,
                    "backup_id": job.backup_id,
                    "artifact": {
                        "type": artifact.get("type", "unknown"),
                        "size_bytes": artifact.get("size_bytes", 0),
                        "size_mb": round(file_size_mb, 2),
                        "hash": artifact.get("hash", ""),
                        "created_at": artifact.get("created_at", "")
                    },
                    "message": f"Backup artifact {artifact.get('type')} created but too large for webhook delivery",
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Send small files as base64 encoded data
                with open(artifact_path, 'rb') as f:
                    file_data = base64.b64encode(f.read()).decode('utf-8')
                
                payload = {
                    "type": "backup_delivery",
                    "job_id": job.job_id,
                    "backup_id": job.backup_id,
                    "artifact": {
                        "type": artifact.get("type", "unknown"),
                        "filename": artifact_path.name,
                        "size_bytes": artifact.get("size_bytes", 0),
                        "hash": artifact.get("hash", ""),
                        "data": file_data,
                        "encoding": "base64"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Mock webhook delivery (in production, use aiohttp)
            delivery_successful = True  # Simulate successful webhook
            
            if delivery_successful:
                return {
                    "channel": channel.name,
                    "artifact": artifact.get("type", "unknown"),
                    "status": "success",
                    "destination": webhook_url,
                    "payload_type": "notification" if file_size_mb > max_size_mb else "full_data",
                    "size_bytes": len(json.dumps(payload)),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "channel": channel.name,
                    "artifact": artifact.get("type", "unknown"),
                    "status": "failed",
                    "error": "Webhook delivery failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "channel": channel.name,
                "artifact": artifact.get("type", "unknown"),
                "status": "failed",
                "error": f"Webhook delivery error: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _record_delivery_job(self, job: DeliveryJob, success: bool):
        """Record delivery job results in database"""
        try:
            # Calculate job statistics
            total_artifacts = len(job.artifacts)
            successful_deliveries = len([r for r in job.delivery_results if r["status"] == "success"])
            failed_deliveries = len([r for r in job.delivery_results if r["status"] == "failed"])
            
            duration_seconds = 0
            if job.completed_at and job.created_at:
                duration_seconds = (job.completed_at - job.created_at).total_seconds()
            
            # Insert into database
            insert_sql = """
            INSERT INTO vault_delivery_jobs 
            (job_id, backup_id, status, total_artifacts, successful_deliveries, 
             failed_deliveries, duration_seconds, delivery_results, created_at, completed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            with self.postgres_agent.connection.cursor() as cur:
                cur.execute(
                    insert_sql,
                    (
                        job.job_id,
                        job.backup_id,
                        job.status,
                        total_artifacts,
                        successful_deliveries,
                        failed_deliveries,
                        duration_seconds,
                        json.dumps(job.delivery_results),
                        job.created_at,
                        job.completed_at
                    )
                )
            self.postgres_agent.connection.commit()
            
            # Publish completion event
            self.publish_event("courier.job_completed", {
                "job_id": job.job_id,
                "backup_id": job.backup_id,
                "status": job.status,
                "success_rate": f"{successful_deliveries}/{total_artifacts}",
                "duration_seconds": duration_seconds
            })
            
        except Exception as e:
            self.logger.error(f"❌ Failed to record delivery job {job.job_id}: {e}")
    
    def _update_delivery_statistics(self, job: DeliveryJob):
        """Update courier delivery statistics"""
        self.total_deliveries += 1
        
        # Count successful artifacts
        successful_artifacts = len([r for r in job.delivery_results if r["status"] == "success"])
        if successful_artifacts == 0:
            self.failed_deliveries += 1
        
        # Update bytes delivered
        for artifact in job.artifacts:
            self.total_bytes_delivered += artifact.get("size_bytes", 0)
        
        # Update average delivery time
        if job.completed_at and job.created_at:
            job_duration = (job.completed_at - job.created_at).total_seconds()
            self.average_delivery_time = (
                (self.average_delivery_time * (self.total_deliveries - 1) + job_duration) / 
                self.total_deliveries
            )
    
    async def _cleanup_job(self, job_id: str, delay_minutes: int = 30):
        """Cleanup completed job after delay"""
        await asyncio.sleep(delay_minutes * 60)
        
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status in ["completed", "failed", "cancelled"]:
                del self.active_jobs[job_id]
                self.logger.debug(f"🧹 Cleaned up delivery job: {job_id}")
    
    async def emergency_evacuation(self, critical_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Emergency evacuation of critical data
        
        Like Paul Revere's midnight ride, this is the fastest possible
        delivery of the most critical data when disaster strikes.
        """
        self.logger.critical("🚨 EMERGENCY EVACUATION PROTOCOL ACTIVATED")
        
        evacuation_id = f"emergency_{int(datetime.utcnow().timestamp())}"
        
        # Create emergency payload
        emergency_payload = {
            "evacuation_id": evacuation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "critical_data": critical_data,
            "fortress_status": "under_siege",
            "priority": "maximum"
        }
        
        # Use all high-priority channels simultaneously  
        emergency_channels = [c for c in self.delivery_channels if c.enabled and c.priority <= 1]
        
        evacuation_results = []
        
        # Execute parallel emergency deliveries
        delivery_tasks = []
        for channel in emergency_channels:
            if channel.type == "webhook":
                # Webhooks are ideal for emergency notifications
                task = self._emergency_webhook_delivery(emergency_payload, channel)
                delivery_tasks.append(task)
        
        if delivery_tasks:
            results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
            
            for result in results:
                if not isinstance(result, Exception):
                    evacuation_results.append(result)
        
        # Log emergency evacuation
        self.publish_event("courier.emergency_evacuation", {
            "evacuation_id": evacuation_id,
            "channels_used": len(emergency_channels),
            "deliveries_attempted": len(delivery_tasks),
            "successful_evacuations": len([r for r in evacuation_results if r.get("status") == "success"])
        })
        
        return {
            "evacuation_id": evacuation_id,
            "status": "completed",
            "emergency_deliveries": evacuation_results,
            "fortress_status": "evacuation_complete"
        }
    
    async def _emergency_webhook_delivery(self, payload: Dict[str, Any], channel: DeliveryChannel) -> Dict[str, Any]:
        """Emergency webhook delivery for critical alerts"""
        try:
            # Mock emergency webhook (use aiohttp in production)
            delivery_successful = True
            
            return {
                "channel": channel.name,
                "type": "emergency_evacuation",
                "status": "success" if delivery_successful else "failed",
                "destination": channel.config["url"],
                "payload_size": len(json.dumps(payload)),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "channel": channel.name,
                "type": "emergency_evacuation", 
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_delivery_status(self) -> Dict[str, Any]:
        """Get current courier status and statistics"""
        
        # Calculate channel statistics
        channel_stats = []
        for channel in self.delivery_channels:
            channel_stats.append({
                "name": channel.name,
                "type": channel.type,
                "enabled": channel.enabled,
                "priority": channel.priority,
                "encryption_required": channel.encryption_required,
                "max_file_size_mb": channel.max_file_size_mb
            })
        
        # Active jobs summary
        active_jobs_summary = {
            "total": len(self.active_jobs),
            "pending": len([j for j in self.active_jobs.values() if j.status == "pending"]),
            "in_progress": len([j for j in self.active_jobs.values() if j.status == "in_progress"]),
            "completed": len([j for j in self.active_jobs.values() if j.status == "completed"]),
            "failed": len([j for j in self.active_jobs.values() if j.status == "failed"])
        }
        
        return {
            "service_running": self.delivery_worker_task is not None,
            "delivery_channels": {
                "total": len(self.delivery_channels),
                "enabled": len([c for c in self.delivery_channels if c.enabled]),
                "channels": channel_stats
            },
            "active_jobs": active_jobs_summary,
            "statistics": {
                "total_deliveries": self.total_deliveries,
                "total_bytes_delivered": self.total_bytes_delivered,
                "failed_deliveries": self.failed_deliveries,
                "success_rate": round((1 - self.failed_deliveries / max(self.total_deliveries, 1)) * 100, 2),
                "average_delivery_time_seconds": round(self.average_delivery_time, 2)
            },
            "queue_size": self.job_queue.qsize()
        }
    
    async def test_delivery_channels(self) -> Dict[str, Any]:
        """Test all configured delivery channels"""
        self.logger.info("🧪 The Courier tests all delivery routes")
        
        test_results = []
        
        # Create test payload
        test_payload = {
            "test_message": "Courier channel test from Vitruvyan Vault",
            "timestamp": datetime.utcnow().isoformat(),
            "test_id": f"test_{int(datetime.utcnow().timestamp())}"
        }
        
        # Test each channel
        for channel in self.delivery_channels:
            if not channel.enabled:
                test_results.append({
                    "channel": channel.name,
                    "status": "skipped",
                    "reason": "channel_disabled"
                })
                continue
            
            try:
                if channel.type == "local":
                    # Test local directory access
                    base_path = Path(channel.config["base_path"])
                    test_file = base_path / "courier_test.json"
                    base_path.mkdir(parents=True, exist_ok=True)
                    
                    with open(test_file, 'w') as f:
                        json.dump(test_payload, f)
                    
                    test_file.unlink()  # Cleanup
                    
                    test_results.append({
                        "channel": channel.name,
                        "status": "success",
                        "test_type": "local_write_test"
                    })
                    
                elif channel.type in ["s3", "gcs"]:
                    # Mock cloud storage tests
                    test_results.append({
                        "channel": channel.name,
                        "status": "success",  # Would test real connection
                        "test_type": f"{channel.type}_connection_test",
                        "note": "Mock test - implement real connection test"
                    })
                    
                elif channel.type == "webhook":
                    # Mock webhook test
                    test_results.append({
                        "channel": channel.name,
                        "status": "success",  # Would test real webhook
                        "test_type": "webhook_ping_test",
                        "note": "Mock test - implement real webhook ping"
                    })
                    
            except Exception as e:
                test_results.append({
                    "channel": channel.name,
                    "status": "failed",
                    "error": str(e)
                })
        
        successful_tests = len([r for r in test_results if r["status"] == "success"])
        total_tests = len(test_results)
        
        self.logger.info(f"🧪 Courier channel tests completed: {successful_tests}/{total_tests} successful")
        
        return {
            "test_completed_at": datetime.utcnow().isoformat(),
            "channels_tested": total_tests,
            "successful_tests": successful_tests,
            "success_rate": round(successful_tests / max(total_tests, 1) * 100, 2),
            "test_results": test_results
        }
    
    def queue_delivery_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Queue a delivery job for processing"""
        try:
            # Calculate queue size safely for job_id
            try:
                queue_size = self.job_queue.qsize() if hasattr(self.job_queue, 'qsize') else len(self.job_queue.queue) if hasattr(self.job_queue, 'queue') else 0
            except:
                queue_size = 0
                
            job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{queue_size}"
            
            # Create artifacts list from backup data
            backup_path = job_data.get("backup_path", "")
            artifacts = []
            
            if backup_path:
                from pathlib import Path
                backup_dir = Path(backup_path)
                
                # Scan backup directory for files
                if backup_dir.exists() and backup_dir.is_dir():
                    for file_path in backup_dir.glob("**/*"):
                        if file_path.is_file():
                            artifacts.append({
                                "type": "backup_file",
                                "path": str(file_path),
                                "size_bytes": file_path.stat().st_size,
                                "name": file_path.name
                            })
                    
                    self.logger.info(f"📦 Found {len(artifacts)} files in backup {backup_path}")
                else:
                    self.logger.warning(f"⚠️ Backup path not found or not a directory: {backup_path}")
            
            if not artifacts:
                self.logger.warning(f"⚠️ No artifacts found for job {job_id}")
            
            delivery_job = DeliveryJob(
                job_id=job_id,
                backup_id=job_data.get("backup_id", "unknown"),
                artifacts=artifacts,
                channels=self.delivery_channels,
                priority=job_data.get("priority", 1),
                created_at=datetime.now(),
                status="pending"
            )
            
            # Queue the job (use put_nowait for sync context)
            self.job_queue.put_nowait(delivery_job)
            
            self.logger.info(f"📮 Delivery job {job_id} queued successfully")
            
            # Calculate queue position safely
            try:
                if hasattr(self.job_queue, 'qsize'):
                    queue_pos = self.job_queue.qsize()
                elif hasattr(self.job_queue, 'queue') and hasattr(self.job_queue.queue, '__len__'):
                    queue_pos = len(self.job_queue.queue) 
                else:
                    queue_pos = 1  # Fallback
            except:
                queue_pos = 1  # Safe fallback
                
            return {
                "success": True,
                "job_id": job_id,
                "delivery_channels": [c.name for c in delivery_job.channels if c.enabled],
                "estimated_duration": len([c for c in delivery_job.channels if c.enabled]) * 30,  # 30s per channel
                "queue_position": queue_pos
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to queue delivery job: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def deliver_backup(self, backup_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Async wrapper for backup delivery - used by Chamberlain"""
        job_data = {
            "backup_path": backup_path,
            "metadata": metadata or {}
        }
        
        return self.queue_delivery_job(job_data)
    
    def __str__(self) -> str:
        active_channels = len([c for c in self.delivery_channels if c.enabled])
        service_status = "delivering" if self.delivery_worker_task else "ready"
        return f"🚀 The Courier - Nuntius Velox ({active_channels} routes, {service_status})"