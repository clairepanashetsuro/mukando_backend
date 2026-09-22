
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    user_role = postgresql.ENUM(
        'TREASURER',
        'MEMBER',
        name='userrole',
        create_type=False
    )

    loan_status = postgresql.ENUM(
        'ACTIVE',
        'PAID',
        'DEFAULTED',
        name='loanstatus',
        create_type=False
    )

    # Create PostgreSQL enum types once
    op.execute(
        "CREATE TYPE userrole AS ENUM ('TREASURER', 'MEMBER')"
    )

    op.execute(
        "CREATE TYPE loanstatus AS ENUM ('ACTIVE', 'PAID', 'DEFAULTED')"
    )

    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(150), nullable=False, unique=True),
        sa.Column('weekly_contribution', sa.Numeric(12, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('full_name', sa.String(150), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', user_role, nullable=False),
        sa.Column(
            'group_id',
            sa.Integer(),
            sa.ForeignKey('groups.id')
        ),
        sa.Column('must_change_password', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'contributions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'member_id',
            sa.Integer(),
            sa.ForeignKey('users.id'),
            nullable=False
        ),
        sa.Column(
            'group_id',
            sa.Integer(),
            sa.ForeignKey('groups.id'),
            nullable=False
        ),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('paid_at', sa.Date(), nullable=False),
        sa.Column(
            'recorded_by',
            sa.Integer(),
            sa.ForeignKey('users.id'),
            nullable=False
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False
        ),
    )

    op.create_table(
        'loans',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'member_id',
            sa.Integer(),
            sa.ForeignKey('users.id'),
            nullable=False
        ),
        sa.Column(
            'group_id',
            sa.Integer(),
            sa.ForeignKey('groups.id'),
            nullable=False
        ),
        sa.Column('principal', sa.Numeric(12, 2), nullable=False),
        sa.Column('interest_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('interest_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', loan_status, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False
        ),
    )

    op.create_table(
        'repayments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'loan_id',
            sa.Integer(),
            sa.ForeignKey('loans.id'),
            nullable=False
        ),
        sa.Column(
            'member_id',
            sa.Integer(),
            sa.ForeignKey('users.id'),
            nullable=False
        ),
        sa.Column(
            'group_id',
            sa.Integer(),
            sa.ForeignKey('groups.id'),
            nullable=False
        ),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('paid_at', sa.Date(), nullable=False),
        sa.Column(
            'recorded_by',
            sa.Integer(),
            sa.ForeignKey('users.id'),
            nullable=False
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False
        ),
    )

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('users.id'),
            nullable=False
        ),
        sa.Column(
            'token_hash',
            sa.String(64),
            nullable=False,
            unique=True
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=False
        ),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False
        ),
    )

    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('users.id'),
            nullable=False
        ),
        sa.Column(
            'token_hash',
            sa.String(64),
            nullable=False,
            unique=True
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=False
        ),
        sa.Column('used', sa.Boolean(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False
        ),
    )


def downgrade():
    for table in [
        'password_reset_tokens',
        'refresh_tokens',
        'repayments',
        'loans',
        'contributions',
        'users',
        'groups',
    ]:
        op.drop_table(table)

    op.execute('DROP TYPE IF EXISTS loanstatus')
    op.execute('DROP TYPE IF EXISTS userrole')

