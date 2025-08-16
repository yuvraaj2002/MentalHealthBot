"""Create chat summaries table

Revision ID: create_chat_summaries_table
Revises: create_performance_indexes
Create Date: 2025-01-27 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'create_chat_summaries_table'
down_revision = 'create_performance_indexes'
branch_labels = None
depends_on = None

def upgrade():
    # Create chat_summaries table
    op.create_table(
        'chat_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance optimization
    op.create_index(
        'idx_chat_summaries_user_chat', 
        'chat_summaries', 
        ['user_id', 'chat_id']
    )
    
    op.create_index(
        'idx_chat_summaries_chat_id', 
        'chat_summaries', 
        ['chat_id']
    )

def downgrade():
    # Drop indexes first
    op.drop_index('idx_chat_summaries_user_chat', table_name='chat_summaries')
    op.drop_index('idx_chat_summaries_chat_id', table_name='chat_summaries')
    
    # Drop table
    op.drop_table('chat_summaries')
