"""add village column and rename area -> village

Revision ID: 20260604addvillage
Revises: 742c657b4fce
Create Date: 2026-06-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260604addvillage'
down_revision = '742c657b4fce'
branch_labels = None
depends_on = None


def upgrade():
    # add village column
    with op.batch_alter_table('anc_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('village', sa.String(length=50), nullable=True))
    # copy existing data from area -> village
    op.execute("UPDATE anc_records SET village = area WHERE village IS NULL AND area IS NOT NULL")
    # update indexes and drop area
    with op.batch_alter_table('anc_records', schema=None) as batch_op:
        # drop old area index if exists
        try:
            batch_op.drop_index(batch_op.f('idx_anc_area'))
        except Exception:
            pass
        batch_op.create_index('idx_anc_village', ['village'], unique=False)
        try:
            batch_op.drop_column('area')
        except Exception:
            pass


def downgrade():
    # add back area column
    with op.batch_alter_table('anc_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('area', sa.String(length=100), nullable=True))
    # copy data back
    op.execute("UPDATE anc_records SET area = village WHERE area IS NULL AND village IS NOT NULL")
    # restore indexes
    with op.batch_alter_table('anc_records', schema=None) as batch_op:
        try:
            batch_op.drop_index(batch_op.f('idx_anc_village'))
        except Exception:
            pass
        batch_op.create_index('idx_anc_area', ['area'], unique=False)
        try:
            batch_op.drop_column('village')
        except Exception:
            pass
