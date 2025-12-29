"""
Pattern Weavers — Weaver Queries Table

Revision ID: 20251109_pattern_weavers
Revises: 20251104_vsgs
Create Date: 2025-11-09 17:30:00

Sacred Order: Pattern Weavers
Epistemic Order: REASON (Semantic Layer)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers
revision = '20251109_pattern_weavers'
down_revision = '20251104_vsgs'
branch_labels = None
depends_on = None


def upgrade():
    """Create weaver_queries table for Pattern Weavers logging."""
    
    op.create_table(
        'weaver_queries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Text(), nullable=False, index=True),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('concepts', JSONB, nullable=True),
        sa.Column('patterns', JSONB, nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False, index=True)
    )
    
    # Index for user_id + created_at queries
    op.create_index(
        'idx_weaver_queries_user_created',
        'weaver_queries',
        ['user_id', 'created_at']
    )
    
    # Index for concept search (GIN index for JSONB)
    op.execute("""
        CREATE INDEX idx_weaver_queries_concepts_gin 
        ON weaver_queries USING GIN (concepts);
    """)
    
    print("✅ Created weaver_queries table with indexes")


def downgrade():
    """Drop weaver_queries table."""
    
    op.drop_index('idx_weaver_queries_concepts_gin', table_name='weaver_queries')
    op.drop_index('idx_weaver_queries_user_created', table_name='weaver_queries')
    op.drop_table('weaver_queries')
    
    print("✅ Dropped weaver_queries table")
