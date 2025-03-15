#!/usr/bin/env python3
"""
Power Snitch UPS Model
Handles UPS configuration, battery health, and alerts.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, 
    CheckConstraint, ForeignKey, func
)
from sqlalchemy.orm import relationship
from web.db import Base

class UPS(Base):
    """UPS model for status monitoring and configuration."""
    
    __tablename__ = 'ups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    model = Column(String(80))
    serial_number = Column(String(80))
    firmware_version = Column(String(80))
    last_update = Column(DateTime, default=datetime.utcnow)
    
    # Current status
    status = Column(String(20))  # online, onbattery, charging, etc.
    battery_charge = Column(Integer)  # percentage
    battery_runtime = Column(Integer)  # seconds
    input_voltage = Column(Float)
    output_voltage = Column(Float)
    load = Column(Integer)  # percentage
    
    # Settings
    low_battery_threshold = Column(Integer, default=20)  # percentage
    critical_battery_threshold = Column(Integer, default=10)  # percentage
    battery_runtime_threshold = Column(Integer, default=300)  # seconds
    
    # Relationships
    battery_history = relationship("BatteryHistory", back_populates="ups", cascade="all, delete-orphan")
    
    def __init__(self, name, model=None, serial_number=None):
        """Initialize a new UPS."""
        self.name = name
        self.model = model
        self.serial_number = serial_number
    
    def update_status(self, status_data):
        """Update UPS status with new data."""
        self.status = status_data.get('status')
        self.battery_charge = status_data.get('battery_charge')
        self.battery_runtime = status_data.get('battery_runtime')
        self.input_voltage = status_data.get('input_voltage')
        self.output_voltage = status_data.get('output_voltage')
        self.load = status_data.get('load')
        self.last_update = datetime.utcnow()
        
        # Create battery history entry
        if self.id and self.battery_charge is not None:
            history = BatteryHistory(
                ups_id=self.id,
                battery_charge=self.battery_charge,
                battery_runtime=self.battery_runtime,
                status=self.status
            )
            history.save()
    
    def get_battery_history(self, limit=24):
        """Get battery history entries."""
        from web.extensions import db
        session = db.get_session()
        try:
            return session.query(BatteryHistory)\
                .filter_by(ups_id=self.id)\
                .order_by(BatteryHistory.timestamp.desc())\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    def save(self):
        """Save UPS to database."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close()
    
    @classmethod
    def get_current_status(cls):
        """Get the current UPS status."""
        from web.extensions import db
        session = db.get_session()
        try:
            return session.query(cls).first()
        finally:
            session.close()
    
    @classmethod
    def get_settings(cls):
        """Get UPS settings."""
        ups = cls.get_current_status()
        if not ups:
            ups = cls(name='Default UPS')
            ups.save()
        return ups
    
    def to_dict(self):
        """Convert UPS to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model,
            'serial_number': self.serial_number,
            'firmware_version': self.firmware_version,
            'last_update': self.last_update.isoformat(),
            'status': self.status,
            'battery_charge': self.battery_charge,
            'battery_runtime': self.battery_runtime,
            'input_voltage': self.input_voltage,
            'output_voltage': self.output_voltage,
            'load': self.load,
            'settings': {
                'low_battery_threshold': self.low_battery_threshold,
                'critical_battery_threshold': self.critical_battery_threshold,
                'battery_runtime_threshold': self.battery_runtime_threshold
            }
        }

class BatteryHistory(Base):
    """Model for storing battery history."""
    
    __tablename__ = 'battery_history'
    
    id = Column(Integer, primary_key=True)
    ups_id = Column(Integer, ForeignKey('ups.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    battery_charge = Column(Integer)
    battery_runtime = Column(Integer)
    status = Column(String(20))
    
    # Relationship
    ups = relationship("UPS", back_populates="battery_history")
    
    def __init__(self, ups_id, battery_charge, battery_runtime, status):
        """Initialize a new battery history entry."""
        self.ups_id = ups_id
        self.battery_charge = battery_charge
        self.battery_runtime = battery_runtime
        self.status = status
    
    def save(self):
        """Save battery history entry to database."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close()
    
    def to_dict(self):
        """Convert battery history entry to dictionary."""
        return {
            'id': self.id,
            'ups_id': self.ups_id,
            'timestamp': self.timestamp.isoformat(),
            'battery_charge': self.battery_charge,
            'battery_runtime': self.battery_runtime,
            'status': self.status
        }

class UPSConfig(Base):
    """UPS configuration model."""
    
    __tablename__ = 'ups_config'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(255))
    poll_interval = Column(Integer, nullable=False, default=5)
    # NUT-specific fields
    nut_device_name = Column(String(80), nullable=False, default='ups')
    nut_driver = Column(String(80), nullable=False, default='usbhid-ups')
    nut_port = Column(String(255))
    nut_username = Column(String(80), nullable=False, default='admin')
    nut_password = Column(String(255), nullable=False)
    nut_retry_count = Column(Integer, default=3)
    nut_retry_delay = Column(Integer, default=5)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    @classmethod
    def get_config(cls):
        """Get UPS configuration."""
        from web.extensions import db
        session = db.get_session()
        try:
            config = session.query(cls).first()
            if not config:
                config = cls(
                    name='UPS',
                    nut_device_name='ups',
                    nut_driver='usbhid-ups',
                    nut_username='admin',
                    nut_password=''
                )
                session.add(config)
                session.commit()
            return config
        finally:
            session.close()
    
    def save(self):
        """Save UPS configuration."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close()
    
    def update(self, **kwargs):
        """Update UPS configuration."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()

class BatteryHealthConfig(Base):
    """Battery health configuration model."""
    
    __tablename__ = 'battery_health_config'
    
    id = Column(Integer, primary_key=True)
    low_charge_threshold = Column(Integer, nullable=False, default=20)
    warning_charge_threshold = Column(Integer, nullable=False, default=50)
    low_runtime_threshold = Column(Integer, nullable=False, default=300)
    low_voltage_threshold = Column(Float)
    high_voltage_threshold = Column(Float)
    temperature_high_threshold = Column(Float)
    temperature_low_threshold = Column(Float)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    @classmethod
    def get_config(cls):
        """Get battery health configuration."""
        from web.extensions import db
        session = db.get_session()
        try:
            config = session.query(cls).first()
            if not config:
                config = cls()
                session.add(config)
                session.commit()
            return config
        finally:
            session.close()
    
    def save(self):
        """Save battery health configuration."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close()
    
    def update(self, **kwargs):
        """Update battery health configuration."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()

class BatteryHealthHistory(Base):
    """Battery health history model."""
    
    __tablename__ = 'battery_health_history'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    charge_percentage = Column(Integer, nullable=False)
    runtime_seconds = Column(Integer)
    voltage = Column(Float)
    current = Column(Float)
    temperature = Column(Float)
    energy_stored = Column(Float)
    energy_full = Column(Float)
    battery_date = Column(String)
    battery_type = Column(String)
    battery_packs = Column(Integer)
    battery_packs_bad = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    @classmethod
    def get_history(cls, limit=24):
        """Get recent battery health history records."""
        from web.extensions import db
        session = db.get_session()
        try:
            return session.query(cls)\
                .order_by(cls.timestamp.desc())\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    def save(self):
        """Save battery health history record."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close()

class BatteryAlert(Base):
    """Battery alert model."""
    
    __tablename__ = 'battery_alerts'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=func.now())
    alert_type = Column(String(50), CheckConstraint("alert_type IN ('low_charge', 'low_runtime', 'low_voltage', 'high_voltage', 'high_temperature', 'low_temperature', 'bad_packs', 'replacement_needed')"), nullable=False)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    @classmethod
    def get_recent_alerts(cls, limit=10):
        """Get recent battery alerts."""
        from web.extensions import db
        session = db.get_session()
        try:
            return session.query(cls)\
                .order_by(cls.timestamp.desc())\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    def save(self):
        """Save battery alert."""
        from web.extensions import db
        session = db.get_session()
        try:
            session.add(self)
            session.commit()
        finally:
            session.close()
    
    def resolve(self):
        """Resolve a battery alert."""
        self.resolved = True
        self.resolved_at = datetime.utcnow()
        self.save() 