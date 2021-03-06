"""blob to string

Revision ID: b3021674b1d2
Revises: dffac63f7ded
Create Date: 2021-02-22 18:07:57.234756

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3021674b1d2'
down_revision = 'dffac63f7ded'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('employee', 'profile_pic',
               existing_type=sa.BLOB(),
               type_=sa.String(length=20),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('employee', 'profile_pic',
               existing_type=sa.String(length=20),
               type_=sa.BLOB(),
               existing_nullable=True)
    # ### end Alembic commands ###
