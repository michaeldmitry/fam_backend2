"""active status to sale

Revision ID: dd8f48beae48
Revises: b27d7f302cf5
Create Date: 2021-04-26 15:53:07.617495

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dd8f48beae48'
down_revision = 'b27d7f302cf5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sale', sa.Column('is_active', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('sale', 'is_active')
    # ### end Alembic commands ###