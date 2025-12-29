"""VSGS PR-B Migration — Introduce semantic_grounding_events table

Sacred Order: Memory Orders
Epistemic Layer: Truth → Archivarium (PostgreSQL) → Mnemosyne (Qdrant)
This transmutation enables persistent semantic grounding and cross-validation with Qdrant.

Revision ID: 20251104_vsgs
Revises: 
Create Date: 2025-11-04 14:00:00.000000

Purpose:
- Enable dual-write persistence (PostgreSQL + Qdrant)
- Track semantic grounding events with trace_id
- Implement phrase_hash deduplication
- Monitor sync status (qdrant_synced flag)
- Support affective state tracking
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision = '20251104_vsgs'
down_revision = None  # Will be updated by AlchemistAgent
branch_labels = None
depends_on = None


def upgrade():
    """
    Create semantic_grounding_events table for VSGS PR-B.
    
    Schema Design:
    - phrase_hash: SHA256(user_id + query_text + language) for deduplication
    - embedding_vector: ARRAY(384 FLOAT) - optional for backfill compatibility
    - qdrant_synced: Boolean flag for Memory Orders sync tracking
    - phase: "ingest", "sync", "enrichment" - lifecycle tracking
    """
    op.create_table(
        'semantic_grounding_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('trace_id', sa.String(length=64), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('language', sa.String(length=8), nullable=True),
        sa.Column('affective_state', sa.String(length=32), nullable=True),
        sa.Column('semantic_context', sa.JSON(), nullable=True),
        sa.Column('embedding_vector', ARRAY(sa.Float()), nullable=True),
        sa.Column('grounding_confidence', sa.Float(), nullable=True),
        sa.Column('phrase_hash', sa.String(length=128), nullable=False),
        sa.Column('phase', sa.String(length=32), nullable=True),
        sa.Column('qdrant_synced', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phrase_hash')
    )
    
    # Create indexes for performance
    op.create_index('idx_grounding_user_id', 'semantic_grounding_events', ['user_id'], unique=False)
    op.create_index('idx_grounding_trace_id', 'semantic_grounding_events', ['trace_id'], unique=False)
    op.create_index('idx_grounding_synced', 'semantic_grounding_events', ['qdrant_synced'], unique=False)
    op.create_index('idx_grounding_phase', 'semantic_grounding_events', ['phase'], unique=False)
    op.create_index('idx_grounding_created', 'semantic_grounding_events', ['created_at'], unique=False)


def downgrade():
    """
    Drop semantic_grounding_events table and indexes.
    
    Safe rollback: No data loss if VSGS_ENABLED=0 during PR-B testing.
    """
    op.drop_index('idx_grounding_created', table_name='semantic_grounding_events')
    op.drop_index('idx_grounding_phase', table_name='semantic_grounding_events')
    op.drop_index('idx_grounding_synced', table_name='semantic_grounding_events')
    op.drop_index('idx_grounding_trace_id', table_name='semantic_grounding_events')
    op.drop_index('idx_grounding_user_id', table_name='semantic_grounding_events')
    op.drop_table('semantic_grounding_events')
