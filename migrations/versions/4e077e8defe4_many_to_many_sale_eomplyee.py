"""many to many sale eomplyee

Revision ID: 4e077e8defe4
Revises: afdcf8d6bd82
Create Date: 2021-03-14 17:28:05.636881

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e077e8defe4'
down_revision = 'afdcf8d6bd82'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sale_employee_association',
    sa.Column('sale_id', sa.Integer(), nullable=False),
    sa.Column('employee_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['employee_id'], ['employee.id'], ),
    sa.ForeignKeyConstraint(['sale_id'], ['sale.id'], ),
    sa.PrimaryKeyConstraint('sale_id', 'employee_id')
    )
    op.drop_column('employee', 'profile_pic')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('employee', sa.Column('profile_pic', sa.BLOB(), nullable=True))
    op.drop_table('sale_employee_association')
    # ### end Alembic commands ###
