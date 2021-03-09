"""string 2

Revision ID: 74631de1fba2
Revises: f269718ed50f
Create Date: 2021-02-22 18:14:12.963187

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '74631de1fba2'
down_revision = 'f269718ed50f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('employee', 'profile_pic',
               existing_type=sa.BLOB(),
               type_=sa.String(length=2),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('employee', 'profile_pic',
               existing_type=sa.String(length=2),
               type_=sa.BLOB(),
               existing_nullable=True)
    # ### end Alembic commands ###
