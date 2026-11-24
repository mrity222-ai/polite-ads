"""complete schema and financial integrity

Revision ID: 81a41b06d412
Revises: 2a808ca65829
Create Date: 2026-10-27 11:55:48.905738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81a41b06d412'
down_revision: Union[str, Sequence[str], None] = '2a808ca65829'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if 'webhook_events' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('webhook_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('signature_verified', sa.Boolean(), nullable=False),
        sa.Column('is_processed', sa.Boolean(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
        )
    if 'ix_webhook_events_event_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('webhook_events')}:
        op.create_index(op.f('ix_webhook_events_event_id'), 'webhook_events', ['event_id'], unique=True)
    if 'ix_webhook_events_event_type' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('webhook_events')}:
        op.create_index(op.f('ix_webhook_events_event_type'), 'webhook_events', ['event_type'], unique=False)
    if 'ix_webhook_events_is_processed' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('webhook_events')}:
        op.create_index(op.f('ix_webhook_events_is_processed'), 'webhook_events', ['is_processed'], unique=False)
    if 'journal_lines' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('journal_lines',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('account', sa.String(length=50), nullable=False),
        sa.Column('debit_paise', sa.Integer(), nullable=False),
        sa.Column('credit_paise', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
    if 'ix_journal_lines_transaction_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('journal_lines')}:
        op.create_index(op.f('ix_journal_lines_transaction_id'), 'journal_lines', ['transaction_id'], unique=False)
    if 'ledger_entries' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('ledger_entries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('tx_type', sa.String(length=50), nullable=False),
        sa.Column('amount_paise', sa.Integer(), nullable=False),
        sa.Column('platform_cut_paise', sa.Integer(), nullable=False),
        sa.Column('meta_spend_paise', sa.Integer(), nullable=False),
        sa.Column('reference_id', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
    if 'ix_ledger_entries_reference_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('ledger_entries')}:
        op.create_index(op.f('ix_ledger_entries_reference_id'), 'ledger_entries', ['reference_id'], unique=False)
    if 'ix_ledger_entries_tx_type' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('ledger_entries')}:
        op.create_index(op.f('ix_ledger_entries_tx_type'), 'ledger_entries', ['tx_type'], unique=False)
    if 'ix_ledger_entries_user_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('ledger_entries')}:
        op.create_index(op.f('ix_ledger_entries_user_id'), 'ledger_entries', ['user_id'], unique=False)
    if 'notifications' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('action_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
    if 'ix_notifications_is_read' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('notifications')}:
        op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    if 'ix_notifications_user_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('notifications')}:
        op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    if 'payment_orders' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('payment_orders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('item_id', sa.String(length=50), nullable=True),
        sa.Column('amount_paise', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('razorpay_order_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
    if 'ix_payment_orders_razorpay_order_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('payment_orders')}:
        op.create_index(op.f('ix_payment_orders_razorpay_order_id'), 'payment_orders', ['razorpay_order_id'], unique=True)
    if 'ix_payment_orders_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('payment_orders')}:
        op.create_index(op.f('ix_payment_orders_status'), 'payment_orders', ['status'], unique=False)
    if 'ix_payment_orders_user_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('payment_orders')}:
        op.create_index(op.f('ix_payment_orders_user_id'), 'payment_orders', ['user_id'], unique=False)
    if 'payments' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('payments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('order_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('amount_paise', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('razorpay_payment_id', sa.String(length=100), nullable=False),
        sa.Column('razorpay_signature', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('refund_reserved_paise', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['payment_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
    if 'ix_payments_order_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('payments')}:
        op.create_index(op.f('ix_payments_order_id'), 'payments', ['order_id'], unique=False)
    if 'ix_payments_razorpay_payment_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('payments')}:
        op.create_index(op.f('ix_payments_razorpay_payment_id'), 'payments', ['razorpay_payment_id'], unique=True)
    if 'ix_payments_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('payments')}:
        op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    if 'ix_payments_user_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('payments')}:
        op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)
    if 'publishing_jobs' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('publishing_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('campaign_id', sa.String(length=36), nullable=False),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('idempotency_key', sa.String(length=64), nullable=False),
        sa.Column('meta_campaign_id', sa.String(length=100), nullable=True),
        sa.Column('meta_adset_id', sa.String(length=100), nullable=True),
        sa.Column('meta_creative_id', sa.String(length=100), nullable=True),
        sa.Column('meta_ad_id', sa.String(length=100), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
    if 'ix_publishing_jobs_campaign_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('publishing_jobs')}:
        op.create_index(op.f('ix_publishing_jobs_campaign_id'), 'publishing_jobs', ['campaign_id'], unique=False)
    if 'ix_publishing_jobs_idempotency_key' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('publishing_jobs')}:
        op.create_index(op.f('ix_publishing_jobs_idempotency_key'), 'publishing_jobs', ['idempotency_key'], unique=True)
    if 'ix_publishing_jobs_stage' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('publishing_jobs')}:
        op.create_index(op.f('ix_publishing_jobs_stage'), 'publishing_jobs', ['stage'], unique=False)
    if 'ix_publishing_jobs_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('publishing_jobs')}:
        op.create_index(op.f('ix_publishing_jobs_status'), 'publishing_jobs', ['status'], unique=False)
    if 'refunds' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('refunds',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('payment_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('amount_paise', sa.Integer(), nullable=False),
        sa.Column('razorpay_refund_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('operation_id', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('operation_id')
        )
    if 'ix_refunds_payment_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('refunds')}:
        op.create_index(op.f('ix_refunds_payment_id'), 'refunds', ['payment_id'], unique=False)
    if 'ix_refunds_razorpay_refund_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('refunds')}:
        op.create_index(op.f('ix_refunds_razorpay_refund_id'), 'refunds', ['razorpay_refund_id'], unique=True)
    if 'ix_refunds_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('refunds')}:
        op.create_index(op.f('ix_refunds_status'), 'refunds', ['status'], unique=False)
    if 'ix_refunds_user_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('refunds')}:
        op.create_index(op.f('ix_refunds_user_id'), 'refunds', ['user_id'], unique=False)
    if 'area' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('campaigns')}:
        op.add_column('campaigns', sa.Column('area', sa.String(length=150), nullable=True))
    if 'pincode' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('campaigns')}:
        op.add_column('campaigns', sa.Column('pincode', sa.String(length=10), nullable=True))
    if 'whatsapp_phone' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('campaigns')}:
        op.add_column('campaigns', sa.Column('whatsapp_phone', sa.String(length=20), nullable=True))
    if 'symbol' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('campaigns')}:
        op.add_column('campaigns', sa.Column('symbol', sa.String(length=100), nullable=True))
    if 'photo_url' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('campaigns')}:
        op.add_column('campaigns', sa.Column('photo_url', sa.Text(), nullable=True))
    if 'company_review_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('campaigns')}:
        op.add_column('campaigns', sa.Column('company_review_status', sa.String(length=40), nullable=False, server_default='Pending'))
    if 'publishing_job_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('campaigns')}:
        op.add_column('campaigns', sa.Column('publishing_job_status', sa.String(length=40), nullable=False, server_default='Queued'))
    if 'provider_review_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('campaigns')}:
        op.add_column('campaigns', sa.Column('provider_review_status', sa.String(length=40), nullable=False, server_default='Pending'))
    if 'delivery_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('campaigns')}:
        op.add_column('campaigns', sa.Column('delivery_status', sa.String(length=40), nullable=False, server_default='Paused'))
    if 'ix_campaigns_company_review_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('campaigns')}:
        op.create_index(op.f('ix_campaigns_company_review_status'), 'campaigns', ['company_review_status'], unique=False)
    if 'ix_campaigns_delivery_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('campaigns')}:
        op.create_index(op.f('ix_campaigns_delivery_status'), 'campaigns', ['delivery_status'], unique=False)
    if 'ix_campaigns_provider_review_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('campaigns')}:
        op.create_index(op.f('ix_campaigns_provider_review_status'), 'campaigns', ['provider_review_status'], unique=False)
    if 'ix_campaigns_publishing_job_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_indexes('campaigns')}:
        op.create_index(op.f('ix_campaigns_publishing_job_status'), 'campaigns', ['publishing_job_status'], unique=False)
    if 'meta_connection_status' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('profiles')}:
        op.add_column('profiles', sa.Column('meta_connection_status', sa.String(length=40), nullable=False, server_default='Not Connected'))
    if 'meta_page_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('profiles')}:
        op.add_column('profiles', sa.Column('meta_page_id', sa.String(length=100), nullable=True))
    if 'meta_page_name' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('profiles')}:
        op.add_column('profiles', sa.Column('meta_page_name', sa.String(length=150), nullable=True))
    if 'meta_access_token_encrypted' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('profiles')}:
        op.add_column('profiles', sa.Column('meta_access_token_encrypted', sa.Text(), nullable=True))
    # Older hand-written schemas allowed null lifecycle fields. Normalize on a copy first.
    for table, defaults in [('campaigns', {'company_review_status':'Pending','publishing_job_status':'Queued','provider_review_status':'Pending','delivery_status':'Paused'}), ('profiles', {'meta_connection_status':'Not Connected'})]:
        nullable = {c['name'] for c in sa.inspect(op.get_bind()).get_columns(table) if c['nullable']}
        for name, default in defaults.items():
            if name in nullable:
                op.execute(sa.text(f'UPDATE {table} SET {name}=:value WHERE {name} IS NULL').bindparams(value=default))
                with op.batch_alter_table(table) as batch:
                    batch.alter_column(name, existing_type=sa.String(40), nullable=False)
    if 'refund_reserved_paise' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('payments')}:
        op.add_column('payments', sa.Column('refund_reserved_paise', sa.Integer(), nullable=False, server_default='0'))
        op.execute(sa.text("UPDATE payments SET refund_reserved_paise = COALESCE((SELECT SUM(amount_paise) FROM refunds WHERE refunds.payment_id=payments.id AND refunds.status IN ('pending','processed')), 0)"))
    if 'operation_id' not in {x['name'] for x in sa.inspect(op.get_bind()).get_columns('refunds')}:
        op.add_column('refunds', sa.Column('operation_id', sa.String(100), nullable=True))
        op.execute(sa.text("UPDATE refunds SET operation_id = 'legacy_' || id"))
        with op.batch_alter_table('refunds') as batch:
            batch.alter_column('operation_id', existing_type=sa.String(100), nullable=False)
            batch.create_unique_constraint('uq_refunds_operation_id', ['operation_id'])
    if not any(fk['constrained_columns'] == ['actor_id'] for fk in sa.inspect(op.get_bind()).get_foreign_keys('audit_events')):
        op.execute(sa.text("UPDATE audit_events SET actor_id=NULL WHERE actor_id IS NOT NULL AND actor_id NOT IN (SELECT id FROM users)"))
        with op.batch_alter_table('audit_events') as batch:
            batch.create_foreign_key('fk_audit_actor', 'users', ['actor_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    raise RuntimeError('Financial history must not be dropped automatically. Restore a verified backup instead.')
