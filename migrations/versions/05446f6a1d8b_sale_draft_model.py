"""sale draft model

Revision ID: 05446f6a1d8b
Revises: 02f4267ff141
Create Date: 2021-04-27 11:13:36.057316

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05446f6a1d8b'
down_revision = '02f4267ff141'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sale_draft',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('total_price', sa.Float(precision=2), nullable=True),
    sa.Column('official', sa.Boolean(), nullable=True),
    sa.Column('orders', sa.JSON(), nullable=True),
    sa.Column('employees_belong', sa.JSON(), nullable=True),
    sa.Column('customer_id', sa.String(length=64), nullable=True),
    sa.Column('taxes_add', sa.Boolean(), nullable=True),
    sa.Column('reduction_add', sa.Boolean(), nullable=True),
    sa.Column('representative_name', sa.String(length=64), nullable=True),
    sa.Column('representative_number', sa.String(length=64), nullable=True),
    sa.Column('representative_email', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('sale_draft')
    # ### end Alembic commands ###
