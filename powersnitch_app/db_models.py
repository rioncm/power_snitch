from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    password_changed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UPSDevice(Base):
    __tablename__ = "ups_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    identifier: Mapped[str] = mapped_column(String, unique=True)
    display_name: Mapped[str] = mapped_column(String)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=15)
    battery_low_pct_threshold: Mapped[float] = mapped_column(Float, default=25)
    runtime_low_threshold_seconds: Mapped[float] = mapped_column(Float, default=300)
    vendor: Mapped[str | None] = mapped_column(String, nullable=True)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    serial: Mapped[str | None] = mapped_column(String, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    rules: Mapped[list["AlertRule"]] = relationship(back_populates="device")


class NotificationService(Base):
    __tablename__ = "notification_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_type: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String, unique=True)
    config_json: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    channels: Mapped[list["NotificationChannel"]] = relationship(back_populates="service")


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("notification_services.id"))
    target_json: Mapped[str] = mapped_column(Text)
    extra_text: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    service: Mapped["NotificationService"] = relationship(back_populates="channels")


class AlertRule(Base):
    __tablename__ = "alert_rules"
    __table_args__ = (
        UniqueConstraint("ups_device_id", "condition_key", "channel_id", name="uq_alert_rule_mapping"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ups_device_id: Mapped[int] = mapped_column(ForeignKey("ups_devices.id"))
    condition_key: Mapped[str] = mapped_column(String)
    channel_id: Mapped[int] = mapped_column(ForeignKey("notification_channels.id"))
    repeat_interval_seconds: Mapped[int] = mapped_column(Integer, default=900)
    send_recovery: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    device: Mapped["UPSDevice"] = relationship(back_populates="rules")
    channel: Mapped["NotificationChannel"] = relationship()


class ActiveCondition(Base):
    __tablename__ = "active_conditions"
    __table_args__ = (
        UniqueConstraint("ups_device_id", "condition_key", name="uq_active_condition"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ups_device_id: Mapped[int] = mapped_column(ForeignKey("ups_devices.id"))
    condition_key: Mapped[str] = mapped_column(String)
    active_since: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_alerted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ups_device_id: Mapped[int | None] = mapped_column(ForeignKey("ups_devices.id"), nullable=True)
    channel_id: Mapped[int | None] = mapped_column(ForeignKey("notification_channels.id"), nullable=True)
    condition_key: Mapped[str] = mapped_column(String)
    condition_state: Mapped[str] = mapped_column(String)
    provider: Mapped[str] = mapped_column(String)
    target: Mapped[str] = mapped_column(String)
    success: Mapped[bool] = mapped_column(Boolean)
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text)


class TelemetrySample(Base):
    __tablename__ = "telemetry_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ups_device_id: Mapped[int] = mapped_column(ForeignKey("ups_devices.id"))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    battery_charge: Mapped[float | None] = mapped_column(Float, nullable=True)
    runtime_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    input_voltage: Mapped[float | None] = mapped_column(Float, nullable=True)
    output_voltage: Mapped[float | None] = mapped_column(Float, nullable=True)
    load_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    status_flags: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[str] = mapped_column(Text)

