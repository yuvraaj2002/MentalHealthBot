"""Create performance indexes

Revision ID: create_performance_indexes
Revises: cd8add754792
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'create_performance_indexes'
down_revision = '810b57ceb44e'
branch_labels = None
depends_on = None

def upgrade():
    # Create composite index for checkins table
    op.create_index(
        'idx_checkins_user_type_time', 
        'checkins', 
        ['user_id', 'checkin_type', 'checkin_time']
    )
    
    # Create index for user_id and checkin_time
    op.create_index(
        'idx_checkins_user_time', 
        'checkins', 
        ['user_id', 'checkin_time']
    )
    
    # Create index for users table id (though primary key is already indexed)
    op.create_index(
        'idx_users_id', 
        'users', 
        ['id']
    )

def downgrade():
    # Drop indexes
    op.drop_index('idx_checkins_user_type_time', table_name='checkins')
    op.drop_index('idx_checkins_user_time', table_name='checkins')
    op.drop_index('idx_users_id', table_name='users')
