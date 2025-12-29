"""
🏛️ Vault Keepers — Alembic Migration
====================================
Sacred Order: MEMORY LAYER
Epistemic Role: Schema versioning and data integrity

Migration: Create external_datasets table
Revision: 001_create_external_datasets
Created: November 3, 2025

This migration creates the external_datasets table to store
financial datasets ingested from external sources (Kaggle, etc.)
into the Archivarium (PostgreSQL).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '001_create_external_datasets'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Create external_datasets table for Kaggle ingestion.
    
    Table stores:
    - Financial time series data (OHLCV)
    - Metadata for traceability
    - Source attribution
    - Ingestion timestamps
    """
    op.create_table(
        'external_datasets',
        
        # Primary key
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        
        # Source attribution
        sa.Column('source', sa.String(255), nullable=False, comment='Data source (e.g., Kaggle, Yahoo Finance)'),
        sa.Column('name', sa.String(255), nullable=False, comment='Dataset name'),
        sa.Column('dataset_type', sa.String(50), nullable=False, comment='Type: financial, sentiment, etc.'),
        
        # Financial data
        sa.Column('ticker', sa.String(20), nullable=True, comment='Stock ticker symbol'),
        sa.Column('date', sa.Date(), nullable=True, comment='Trading date'),
        sa.Column('open', sa.Float(), nullable=True, comment='Opening price'),
        sa.Column('close', sa.Float(), nullable=True, comment='Closing price'),
        sa.Column('high', sa.Float(), nullable=True, comment='High price'),
        sa.Column('low', sa.Float(), nullable=True, comment='Low price'),
        sa.Column('volume', sa.Float(), nullable=True, comment='Trading volume'),
        
        # Metadata
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional metadata as JSON'),
        
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # Table metadata
        schema=None,
        comment='External datasets ingested from Kaggle and other sources'
    )
    
    # Create indexes for performance
    op.create_index('idx_external_datasets_ticker', 'external_datasets', ['ticker'])
    op.create_index('idx_external_datasets_date', 'external_datasets', ['date'])
    op.create_index('idx_external_datasets_source', 'external_datasets', ['source'])
    op.create_index('idx_external_datasets_type', 'external_datasets', ['dataset_type'])
    op.create_index('idx_external_datasets_ticker_date', 'external_datasets', ['ticker', 'date'])
    
    # Create GIN index for JSONB metadata search
    op.create_index('idx_external_datasets_metadata_gin', 'external_datasets', ['metadata'], postgresql_using='gin')
    
    print("✅ [Vault Keepers] Created external_datasets table")
    print("✅ [Vault Keepers] Created 6 indexes for query optimization")


def downgrade():
    """
    Drop external_datasets table and all indexes.
    """
    # Drop indexes first
    op.drop_index('idx_external_datasets_metadata_gin', table_name='external_datasets')
    op.drop_index('idx_external_datasets_ticker_date', table_name='external_datasets')
    op.drop_index('idx_external_datasets_type', table_name='external_datasets')
    op.drop_index('idx_external_datasets_source', table_name='external_datasets')
    op.drop_index('idx_external_datasets_date', table_name='external_datasets')
    op.drop_index('idx_external_datasets_ticker', table_name='external_datasets')
    
    # Drop table
    op.drop_table('external_datasets')
    
    print("✅ [Vault Keepers] Dropped external_datasets table and indexes")


# Epistemic Note:
# The Vault Keepers maintain the sacred schema of Archivarium.
# Every migration is a deliberate evolution of the system's memory structure,
# ensuring that knowledge persists across time without corruption or loss.
