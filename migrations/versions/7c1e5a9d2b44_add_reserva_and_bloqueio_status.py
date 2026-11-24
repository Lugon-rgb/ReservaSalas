from alembic import op
import sqlalchemy as sa


revision = '7c1e5a9d2b44'
down_revision = '23e6ca440dd5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('reserva', schema=None) as batch_op:
        batch_op.add_column(sa.Column('situacao', sa.String(length=20), nullable=False, server_default='CONFIRMADA'))
        batch_op.add_column(sa.Column('recursos', sa.JSON(), nullable=False, server_default='[]'))
        batch_op.add_column(sa.Column('entrada', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('saida', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('motivo_cancelamento', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('cancelada_por', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('cancelada_em', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('bloqueio_id', sa.Integer(), nullable=True))

    with op.batch_alter_table('bloqueio', schema=None) as batch_op:
        batch_op.add_column(sa.Column('situacao', sa.String(length=20), nullable=False, server_default='ATIVO'))
        batch_op.add_column(sa.Column('criado_por', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('retirado_por', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('retirado_em', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('bloqueio', schema=None) as batch_op:
        batch_op.drop_column('retirado_em')
        batch_op.drop_column('retirado_por')
        batch_op.drop_column('criado_por')
        batch_op.drop_column('situacao')

    with op.batch_alter_table('reserva', schema=None) as batch_op:
        batch_op.drop_column('bloqueio_id')
        batch_op.drop_column('cancelada_em')
        batch_op.drop_column('cancelada_por')
        batch_op.drop_column('motivo_cancelamento')
        batch_op.drop_column('saida')
        batch_op.drop_column('entrada')
        batch_op.drop_column('recursos')
        batch_op.drop_column('situacao')