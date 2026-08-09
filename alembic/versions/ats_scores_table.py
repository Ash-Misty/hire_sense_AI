"""create ats_scores table

Revision ID: c3d4e5f6a7b8
Revises: b7c8d9e0f1a2
Create Date: 2026-08-10 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ats_scores',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('resume_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('category_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('feedback', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('score_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resume_id', name='uq_ats_scores_resume_id'),
    )
    op.create_index(
        op.f('ix_ats_scores_resume_id'),
        'ats_scores',
        ['resume_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_ats_scores_user_id'),
        'ats_scores',
        ['user_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_ats_scores_user_id'), table_name='ats_scores')
    op.drop_index(op.f('ix_ats_scores_resume_id'), table_name='ats_scores')
    op.drop_table('ats_scores')
