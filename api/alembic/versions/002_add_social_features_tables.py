"""Add social features tables for gamification

Revision ID: 002_social_features
Revises: 001_gamification
Create Date: 2024-12-21 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_social_features'
down_revision = '001_gamification'
branch_labels = None
depends_on = None


def upgrade():
    """Add social features tables"""
    
    # Create achievement_shares table
    op.create_table(
        'achievement_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_achievement_id', sa.Integer(), nullable=False),
        sa.Column('shared_by_user_id', sa.Integer(), nullable=False),
        sa.Column('share_message', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=False),
        sa.Column('share_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_achievement_id'], ['user_achievements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_by_user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_achievement_shares_id', 'achievement_shares', ['id'])
    op.create_index('ix_achievement_shares_user_achievement_id', 'achievement_shares', ['user_achievement_id'])
    op.create_index('ix_achievement_shares_shared_by_user_id', 'achievement_shares', ['shared_by_user_id'])
    
    # Create leaderboards table
    op.create_table(
        'leaderboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('leaderboard_type', sa.String(), nullable=False),
        sa.Column('scope_id', sa.Integer(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('experience_points', sa.Integer(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('is_visible', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, default=False),
        sa.Column('rank_change', sa.Integer(), nullable=False, default=0),
        sa.Column('last_rank_update', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['profile_id'], ['user_gamification_profiles.id'], ondelete='CASCADE')
    )
    op.create_index('ix_leaderboards_id', 'leaderboards', ['id'])
    op.create_index('ix_leaderboards_profile_id', 'leaderboards', ['profile_id'])
    op.create_index('ix_leaderboards_leaderboard_type', 'leaderboards', ['leaderboard_type'])
    op.create_index('ix_leaderboards_scope_id', 'leaderboards', ['scope_id'])
    op.create_index('ix_leaderboards_rank', 'leaderboards', ['rank'])
    op.create_index('ix_leaderboards_updated_at', 'leaderboards', ['updated_at'])
    
    # Create group_challenges table
    op.create_table(
        'group_challenges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('group_type', sa.String(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('group_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_participants', sa.Integer(), nullable=True),
        sa.Column('current_participants', sa.Integer(), nullable=False, default=0),
        sa.Column('group_reward_xp', sa.Integer(), nullable=False, default=0),
        sa.Column('individual_reward_xp', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['challenge_id'], ['challenges.id'], ondelete='CASCADE')
    )
    op.create_index('ix_group_challenges_id', 'group_challenges', ['id'])
    op.create_index('ix_group_challenges_challenge_id', 'group_challenges', ['challenge_id'])
    op.create_index('ix_group_challenges_group_type', 'group_challenges', ['group_type'])
    op.create_index('ix_group_challenges_group_id', 'group_challenges', ['group_id'])
    
    # Create group_challenge_participants table
    op.create_table(
        'group_challenge_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_challenge_id', sa.Integer(), nullable=False),
        sa.Column('user_challenge_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('contribution_points', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['group_challenge_id'], ['group_challenges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_challenge_id'], ['user_challenges.id'], ondelete='CASCADE')
    )
    op.create_index('ix_group_challenge_participants_id', 'group_challenge_participants', ['id'])
    op.create_index('ix_group_challenge_participants_group_challenge_id', 'group_challenge_participants', ['group_challenge_id'])
    op.create_index('ix_group_challenge_participants_user_challenge_id', 'group_challenge_participants', ['user_challenge_id'])


def downgrade():
    """Remove social features tables"""
    
    # Drop tables in reverse order of creation
    op.drop_table('group_challenge_participants')
    op.drop_table('group_challenges')
    op.drop_table('leaderboards')
    op.drop_table('achievement_shares')
