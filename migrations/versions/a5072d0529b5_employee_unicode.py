"""employee unicode

Revision ID: a5072d0529b5
Revises: 4e077e8defe4
Create Date: 2021-03-14 18:46:20.788238

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a5072d0529b5'
down_revision = '4e077e8defe4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('employee', 'address',
               existing_type=mysql.VARCHAR(length=256),
               type_=sa.Unicode(length=128),
               existing_nullable=True)
    op.alter_column('employee', 'fullname',
               existing_type=mysql.VARCHAR(length=256),
               type_=sa.Unicode(length=128),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('employee', 'fullname',
               existing_type=sa.Unicode(length=128),
               type_=mysql.VARCHAR(length=256),
               existing_nullable=False)
    op.alter_column('employee', 'address',
               existing_type=sa.Unicode(length=128),
               type_=mysql.VARCHAR(length=256),
               existing_nullable=True)
    # ### end Alembic commands ###