"""
🏰 BASE KEEPER - Foundation of the Vault Keepers
===============================================
Custos Fundamentum - The Foundation Guardian

Base class for all Vault Keepers, providing common fortress infrastructure:
- PostgresAgent integration for fortress records
- QdrantAgent integration for vector vault  
- Event system for keeper coordination
- Backup modes and configuration management

Like the master mason who lays the foundation stones of a great fortress,
BaseKeeper provides the unshakeable base for all guardian operations.
"""

import asyncio
import logging
import hashlib
import gzip
import tarfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import json
import os

# Vitruvyan Agent Foundation
from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.persistence.qdrant_agent import QdrantAgent

logger = logging.getLogger(__name__)

class BackupMode(Enum):
    """The Four Sacred Modes of Vault Protection"""
    INCREMENTAL = "incremental"          # Every 30 min - Swift patrols
    CRITICAL = "critical"                # Every 6 hours - Battle readiness  
    FULL_SYSTEM = "full_system"          # Daily - Complete fortress survey
    DISASTER_RECOVERY = "disaster_recovery"  # On-demand - Emergency evacuation

class VaultStatus(Enum):
    """Status of Vault Operations"""
    INITIATED = "initiated"
    WATCHING = "watching"
    SEALING = "sealing" 
    DEPARTING = "departing"
    SECURING = "securing"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"

@dataclass
class VaultConfig:
    """Configuration for the Fortress Vault System"""
    
    # Vault Operations
    backup_mode: str = "auto"
    backup_storage: str = "/var/vitruvyan/vaults"
    backup_interval_minutes: int = 30
    
    # Cloud Treasury
    cloud_provider: str = "local"  # local, aws, backblaze, minio
    s3_bucket: str = "vitruvyan-vaults"
    s3_region: str = "eu-west-1" 
    s3_access_key: str = ""
    s3_secret_key: str = ""
    
    # Google Drive (OAuth support)
    gdrive_use_oauth: bool = True  # NEW: Use OAuth instead of Service Account
    gdrive_token_path: str = "/app/secrets/token.json"  # OAuth token
    gdrive_service_account_path: str = "/app/secrets/gdrive-service-account.json"  # Legacy
    
    # Fortress Database
    postgres_host: str = "172.17.0.1"
    postgres_port: int = 5432
    postgres_db: str = "vitruvyan"
    postgres_user: str = "vitruvyan_user"
    postgres_password: str = ""
    
    # Vector Vault
    qdrant_host: str = "vitruvyan_qdrant"
    qdrant_port: int = 6333
    
    @classmethod
    def from_env(cls) -> 'VaultConfig':
        """Load configuration from environment like a royal decree"""
        return cls(
            backup_mode=os.getenv("BACKUP_MODE", "auto"),
            backup_storage=os.getenv("BACKUP_STORAGE", "/var/vitruvyan/vaults"),
            backup_interval_minutes=int(os.getenv("BACKUP_INTERVAL_MINUTES", "30")),
            cloud_provider=os.getenv("BACKUP_CLOUD_PROVIDER", "local"),
            s3_bucket=os.getenv("BACKUP_S3_BUCKET", "vitruvyan-vaults"),
            s3_region=os.getenv("BACKUP_S3_REGION", "eu-west-1"),
            gdrive_use_oauth=os.getenv("GDRIVE_USE_OAUTH", "true").lower() == "true",
            gdrive_token_path=os.getenv("GDRIVE_TOKEN_PATH", "/app/secrets/token.json"),
            gdrive_service_account_path=os.getenv("GDRIVE_SERVICE_ACCOUNT_PATH", "/app/secrets/gdrive-service-account.json"),
            s3_access_key=os.getenv("BACKUP_S3_KEY", ""),
            s3_secret_key=os.getenv("BACKUP_S3_SECRET", ""),
            postgres_host=os.getenv("POSTGRES_HOST", "172.17.0.1"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_db=os.getenv("POSTGRES_DB", "vitruvyan"),
            postgres_user=os.getenv("POSTGRES_USER", "vitruvyan_user"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
            qdrant_host=os.getenv("QDRANT_HOST", "vitruvyan_qdrant"),
            qdrant_port=int(os.getenv("QDRANT_PORT", "6333"))
        )

@dataclass  
class VaultEvent:
    """Event system for Keeper coordination"""
    event_type: str                    # Type of vault event
    keeper: str                        # Which keeper generated event
    payload: Dict[str, Any]            # Event data
    context: Dict[str, Any]            # Additional context
    timestamp: str                     # When event occurred
    fortress_id: Optional[str] = None  # Backup session ID
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for storage"""
        return asdict(self)

@dataclass
class VaultRecord:
    """Database record structure for vault_history table"""
    backup_type: str
    file_path: str
    file_hash: str
    size_mb: float
    duration_s: float
    triggered_by: str
    keeper_crew: str                   # Which keepers were involved
    status: str = "completed"
    fortress_session: Optional[str] = None
    created_at: Optional[datetime] = None

class BaseKeeper:
    """
    Base class for all Vault Keepers
    
    Like the master architect of Carcassonne who designed the fortress walls,
    BaseKeeper provides the foundational infrastructure for all guardian operations.
    
    Responsibilities:
    - Database connectivity via PostgresAgent
    - Vector storage via QdrantAgent  
    - Event publishing and handling
    - Configuration management
    - Logging and error handling
    """
    
    def __init__(self, config: Optional[VaultConfig] = None):
        self.config = config or VaultConfig.from_env()
        
        # Fortress Infrastructure
        self.postgres_agent = PostgresAgent()
        self.qdrant_agent = QdrantAgent()
        
        # Keeper Identity
        self.keeper_name = self.__class__.__name__
        self.keeper_title = self._get_keeper_title()
        
        # Logging
        self.logger = logging.getLogger(f"VaultKeeper.{self.keeper_name}")
        self.logger.info(f"🏰 {self.keeper_title} stands ready to guard the vault")
        
        # Initialize vault infrastructure
        self._initialize_fortress_records()
    
    def _get_keeper_title(self) -> str:
        """Get the medieval title for this keeper"""
        titles = {
            "SentinelAgent": "The Sentinel - Vigil Arcis",
            "ArchivistAgent": "The Archivist - Custos Librorum", 
            "CourierAgent": "The Courier - Nuntius Expeditus",
            "ChamberlainAgent": "The Chamberlain - Camerarius Magnus",
            "BaseKeeper": "The Foundation - Custos Fundamentum"
        }
        return titles.get(self.keeper_name, f"The {self.keeper_name}")
    
    def _initialize_fortress_records(self):
        """Initialize the vault_history table using PostgresAgent - disabled as tables already exist"""
        # Tables are already created manually: vault_keepers_history, vault_keepers_events, etc.
        # This method is disabled to avoid conflicts with existing schema
        self.logger.info("✅ Using existing Vault Keepers database schema")
    
    def publish_event(self, event_type: str, payload: Dict[str, Any], 
                     context: Optional[Dict[str, Any]] = None) -> VaultEvent:
        """
        Publish a vault event to coordinate keepers
        
        Like a herald announcing royal decrees throughout the fortress,
        this method broadcasts important events to all keepers.
        """
        event = VaultEvent(
            event_type=event_type,
            keeper=self.keeper_name,
            payload=payload,
            context=context or {},
            timestamp=datetime.utcnow().isoformat(),
        )
        
        self.logger.info(f"📯 {self.keeper_title} announces: {event_type}")
        
        # Store event in fortress records for audit trail
        try:
            self._log_event_to_fortress(event)
        except Exception as e:
            self.logger.warning(f"⚠️ Could not log event to fortress: {e}")
        
        return event
    
    def _log_event_to_fortress(self, event: VaultEvent):
        """Log vault event to database for audit trail"""
        insert_sql = """
        INSERT INTO vault_keepers_events 
        (event_type, event_source, event_data, priority)
        VALUES (%s, %s, %s, %s)
        """
        
        # Prepare event data
        event_data = {
            "keeper": event.keeper,
            "payload": event.payload,
            "context": event.context,
            "timestamp": event.timestamp,
            "fortress_session": event.fortress_id
        }
        
        try:
            with self.postgres_agent.connection.cursor() as cur:
                cur.execute(insert_sql, (
                event.event_type,
                event.keeper,
                json.dumps(event_data),
                1  # default priority
            ))
        except Exception as e:
            self.logger.error(f"Failed to log event: {e}")
    
    def record_vault_operation(self, record: VaultRecord) -> int:
        """
        Record a completed vault operation in fortress records
        
        Like a scribe carefully documenting royal treasures in the ledger,
        this method maintains the official record of all vault operations.
        """
        insert_sql = """
        INSERT INTO vault_history 
        (backup_type, file_path, file_hash, size_mb, duration_s, 
         triggered_by, keeper_crew, status, fortress_session)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        try:
            with self.postgres_agent.connection.cursor() as cur:
                cur.execute(insert_sql, (
                    record.backup_type,
                    record.file_path, 
                    record.file_hash,
                    record.size_mb,
                    record.duration_s,
                    record.triggered_by,
                    record.keeper_crew,
                    record.status,
                    record.fortress_session
                ))
                result = cur.fetchone()
                self.postgres_agent.connection.commit()
                
                if result:
                    vault_id = result[0]
                    self.logger.info(f"📜 Vault operation recorded in fortress ledger (ID: {vault_id})")
                    return vault_id
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to record vault operation: {e}")
            self.postgres_agent.connection.rollback()
            
        return -1
    
    def get_vault_history(self, limit: int = 50, backup_type: Optional[str] = None) -> List[Dict]:
        """Get recent vault history from fortress records"""
        base_sql = """
        SELECT * FROM vault_history 
        WHERE (%s IS NULL OR backup_type = %s)
        ORDER BY created_at DESC 
        LIMIT %s;
        """
        
        try:
            result = self.postgres_agent.fetch_all(base_sql + f" LIMIT {limit}", (backup_type, backup_type))
            if result:
                columns = ['id', 'backup_type', 'file_path', 'file_hash', 'size_mb',
                          'duration_s', 'triggered_by', 'keeper_crew', 'status', 
                          'fortress_session', 'created_at']
                return [dict(zip(columns, row)) for row in result]
            return []
        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve vault history: {e}")
            return []
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of a file
        
        Like a master jeweler inspecting precious gems for authenticity,
        this method creates an unforgiveable fingerprint of our treasures.
        """
        hash_sha256 = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def get_file_size_mb(self, file_path: str) -> float:
        """Get file size in megabytes"""
        try:
            size_bytes = os.path.getsize(file_path)
            return round(size_bytes / (1024 * 1024), 2)
        except Exception as e:
            self.logger.error(f"❌ Failed to get size for {file_path}: {e}")
            return 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform keeper health check
        
        Like a captain inspecting the fortress walls for weaknesses,
        this method ensures all keeper systems are ready for duty.
        """
        health = {
            "keeper": self.keeper_name,
            "title": self.keeper_title,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "systems": {}
        }
        
        # Check PostgresAgent connection  
        try:
            result = self.postgres_agent.fetch_all("SELECT 1", ())
            health["systems"]["postgres"] = "connected" if result else "error"
        except Exception as e:
            health["systems"]["postgres"] = f"error: {str(e)}"
            health["status"] = "degraded"
        
        # Check QdrantAgent connection
        try:
            qdrant_health = self.qdrant_agent.health()
            health["systems"]["qdrant"] = qdrant_health.get("status", "unknown")
            if qdrant_health.get("status") != "ok":
                health["status"] = "degraded"
        except Exception as e:
            health["systems"]["qdrant"] = f"error: {str(e)}"
            health["status"] = "degraded"
        
        # Check vault storage
        try:
            vault_path = Path(self.config.backup_storage)
            if vault_path.exists() and vault_path.is_dir():
                health["systems"]["vault_storage"] = "accessible"
            else:
                health["systems"]["vault_storage"] = "not_accessible"
                health["status"] = "degraded"
        except Exception as e:
            health["systems"]["vault_storage"] = f"error: {str(e)}"
            health["status"] = "degraded"
        
        return health
    
    def __str__(self) -> str:
        return f"🏰 {self.keeper_title} - Guardian of Vitruvyan Vault"
    
    def __repr__(self) -> str:
        return f"BaseKeeper(name='{self.keeper_name}', title='{self.keeper_title}')"