"""description to order price quota

Revision ID: b27d7f302cf5
Revises: c0fe95f87211
Create Date: 2021-04-25 20:18:59.711085

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b27d7f302cf5'
down_revision = 'c0fe95f87211'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order_price_quota', sa.Column('description', sa.Unicode(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('order_price_quota', 'description')
    # ### end Alembic commands ###
