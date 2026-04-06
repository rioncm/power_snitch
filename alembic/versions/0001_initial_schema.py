"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("password_changed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "ups_devices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("identifier", sa.String(), nullable=False, unique=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("poll_interval_seconds", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("battery_low_pct_threshold", sa.Float(), nullable=False, server_default="25"),
        sa.Column("runtime_low_threshold_seconds", sa.Float(), nullable=False, server_default="300"),
        sa.Column("vendor", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("serial", sa.String(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_snapshot_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "notification_services",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("service_type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "notification_channels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("notification_services.id"), nullable=False),
        sa.Column("target_json", sa.Text(), nullable=False),
        sa.Column("extra_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ups_device_id", sa.Integer(), sa.ForeignKey("ups_devices.id"), nullable=False),
        sa.Column("condition_key", sa.String(), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("notification_channels.id"), nullable=False),
        sa.Column("repeat_interval_seconds", sa.Integer(), nullable=False, server_default="900"),
        sa.Column("send_recovery", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("ups_device_id", "condition_key", "channel_id", name="uq_alert_rule_mapping"),
    )
    op.create_table(
        "active_conditions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ups_device_id", sa.Integer(), sa.ForeignKey("ups_devices.id"), nullable=False),
        sa.Column("condition_key", sa.String(), nullable=False),
        sa.Column("active_since", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_alerted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_value", sa.Text(), nullable=True),
        sa.Column("last_reason", sa.Text(), nullable=True),
        sa.UniqueConstraint("ups_device_id", "condition_key", name="uq_active_condition"),
    )
    op.create_table(
        "alert_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ups_device_id", sa.Integer(), sa.ForeignKey("ups_devices.id"), nullable=True),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("notification_channels.id"), nullable=True),
        sa.Column("condition_key", sa.String(), nullable=False),
        sa.Column("condition_state", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("target", sa.String(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
    )
    op.create_table(
        "telemetry_samples",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ups_device_id", sa.Integer(), sa.ForeignKey("ups_devices.id"), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("battery_charge", sa.Float(), nullable=True),
        sa.Column("runtime_seconds", sa.Float(), nullable=True),
        sa.Column("input_voltage", sa.Float(), nullable=True),
        sa.Column("output_voltage", sa.Float(), nullable=True),
        sa.Column("load_percent", sa.Float(), nullable=True),
        sa.Column("status_flags", sa.Text(), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("telemetry_samples")
    op.drop_table("alert_events")
    op.drop_table("active_conditions")
    op.drop_table("alert_rules")
    op.drop_table("notification_channels")
    op.drop_table("notification_services")
    op.drop_table("ups_devices")
    op.drop_table("app_settings")
    op.drop_table("users")
