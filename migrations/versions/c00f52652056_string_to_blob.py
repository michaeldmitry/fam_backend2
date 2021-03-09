"""string to blob

Revision ID: c00f52652056
Revises: b3021674b1d2
Create Date: 2021-02-22 18:08:15.961020

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'c00f52652056'
down_revision = 'b3021674b1d2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('employee', 'profile_pic',
               existing_type=mysql.VARCHAR(length=20),
               type_=sa.LargeBinary(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('employee', 'profile_pic',
               existing_type=sa.LargeBinary(),
               type_=mysql.VARCHAR(length=20),
               existing_nullable=True)
    # ### end Alembic commands ###
