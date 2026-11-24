"""Add building floor range and user name

Revision ID: 4b5f01f3606e
Revises: 89fc0a1c4e59
Create Date: 2026-11-23 13:16:41.677915

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b5f01f3606e'
down_revision = '89fc0a1c4e59'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('edificio', schema=None) as batch_op:
        batch_op.add_column(sa.Column('andar_minimo', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('andar_maximo', sa.Integer(), nullable=True))

    op.execute(
        'UPDATE edificio SET andar_minimo = 1, andar_maximo = andares'
    )

    with op.batch_alter_table('edificio', schema=None) as batch_op:
        batch_op.alter_column('andar_minimo', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('andar_maximo', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('andares')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nome', sa.String(length=100), nullable=True))

    op.execute('UPDATE "user" SET nome = matricula')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('nome', existing_type=sa.String(length=100), nullable=False)


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('nome')

    with op.batch_alter_table('edificio', schema=None) as batch_op:
        batch_op.add_column(sa.Column('andares', sa.Integer(), nullable=True))

    op.execute('UPDATE edificio SET andares = andar_maximo - andar_minimo + 1')

    with op.batch_alter_table('edificio', schema=None) as batch_op:
        batch_op.alter_column('andares', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('andar_maximo')
        batch_op.drop_column('andar_minimo')
