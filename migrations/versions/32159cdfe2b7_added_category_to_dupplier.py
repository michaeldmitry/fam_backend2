"""added category to dupplier

Revision ID: 32159cdfe2b7
Revises: 8ddc094123fb
Create Date: 2021-02-05 07:32:08.547824

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32159cdfe2b7'
down_revision = '8ddc094123fb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('supplier_category_association',
    sa.Column('supplier_id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['client.id'], ),
    sa.PrimaryKeyConstraint('supplier_id', 'category_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('supplier_category_association')
    # ### end Alembic commands ###
