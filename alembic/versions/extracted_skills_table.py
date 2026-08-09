"""create extracted_skills table

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-08-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'extracted_skills',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('resume_id', sa.UUID(), nullable=False),
        sa.Column('skill', sa.String(length=255), nullable=False),
        sa.Column('normalized_skill', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'],
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'resume_id', 'normalized_skill',
            name='uq_extracted_skills_resume_skill',
        ),
    )
    op.create_index(
        op.f('ix_extracted_skills_category'),
        'extracted_skills', ['category'], unique=False,
    )
    op.create_index(
        op.f('ix_extracted_skills_normalized_skill'),
        'extracted_skills', ['normalized_skill'], unique=False,
    )
    op.create_index(
        op.f('ix_extracted_skills_resume_id'),
        'extracted_skills', ['resume_id'], unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_extracted_skills_resume_id'),
                  table_name='extracted_skills')
    op.drop_index(op.f('ix_extracted_skills_normalized_skill'),
                  table_name='extracted_skills')
    op.drop_index(op.f('ix_extracted_skills_category'),
                  table_name='extracted_skills')
    op.drop_table('extracted_skills')

