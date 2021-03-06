"""float precision

Revision ID: 76cbfa9c3701
Revises: a5072d0529b5
Create Date: 2021-03-14 19:16:46.271644

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '76cbfa9c3701'
down_revision = 'a5072d0529b5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('order_customer', 'price_per_item',
               existing_type=mysql.FLOAT(),
               type_=sa.String(length=20),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('order_customer', 'price_per_item',
               existing_type=sa.String(length=20),
               type_=mysql.FLOAT(),
               existing_nullable=True)
    # ### end Alembic commands ###
