"""large binary

Revision ID: 4364f95aa315
Revises: 74631de1fba2
Create Date: 2021-02-22 18:14:46.373111

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4364f95aa315'
down_revision = '74631de1fba2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('employee', 'profile_pic',
               existing_type=mysql.VARCHAR(length=2),
               type_=sa.LargeBinary(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('employee', 'profile_pic',
               existing_type=sa.LargeBinary(),
               type_=mysql.VARCHAR(length=2),
               existing_nullable=True)
    # ### end Alembic commands ###