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
import logging

logger = logging.getLogger(__name__)

class UPS(Base):
    """UPS model for status monitoring and configuration."""
    
    __tablename__ = 'ups'
    
    # Basic Information
    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=True)
    manufacturer = Column(String(255))  # device.mfr
    model = Column(String(255))         # device.model
    battery_type = Column(String(255))  # battery.type
    
    # Configuration
    driver = Column(String(80), nullable=False, default='usbhid-ups')
    polling_interval = Column(Integer, default=10)  # seconds
    all_info = Column(String()) #JSON string of all info
    low_battery_threshold = Column(Integer, default=30)
    critical_battery_threshold = Column(Integer, default=10)
    battery_runtime_threshold = Column(Integer, default=300)
    
    # Timestamps
    last_poll = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    

    # Relationships
    battery_history = relationship("BatteryHistory", back_populates="ups", cascade="all, delete-orphan")
    
    def __init__(self):
        """Initialize a new UPS instance."""
        
    
    @classmethod
    def get_config(cls, session):
        """Get UPS configuration or create a default one if it doesn't exist."""
        ups = session.query(cls).first()
        if not ups:
            logger.error("UPS configuration not found in the database. Run install again.")
            raise ValueError("UPS configuration not found in the database.")
        cls.manufacturer = ups.manufacturer
        cls.model = ups.model
        cls.description = ups.description
        return ups
    
    def record_status(self, status_data):
        """Record current UPS status in battery history."""
        try:
            history = BatteryHistory(
                status=status_data.get('ups.status'),
                battery_charge=float(status_data.get('battery.charge', 0)),
                estimated_runtime=int(status_data.get('battery.runtime', 0)),
                load=float(status_data.get('ups.load', 0)),
                input_voltage=float(status_data.get('input.voltage', 0)),
                output_voltage=float(status_data.get('output.voltage', 0))
            )
            self.battery_history.append(history)
            self.last_poll = func.now()
            
            logger.info(f"Recorded UPS status: {status_data.get('ups.status', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to record UPS status: {str(e)}")
            return False
    
    def update_info(self, nut_data):
        """Update static UPS information from NUT data."""
        try:
            if 'device.mfr' in nut_data:
                self.manufacturer = nut_data['device.mfr']
            if 'device.model' in nut_data:
                self.model = nut_data['device.model']
            if 'battery.type' in nut_data:
                self.battery_type = nut_data['battery.type']
            if 'ups.serial' in nut_data:
                self.serial_number = nut_data['ups.serial']
            if 'ups.firmware' in nut_data:
                self.firmware = nut_data['ups.firmware']
            if 'driver.name' in nut_data:
                self.driver = nut_data['driver.name']
            
            logger.info(f"Updated UPS info for {self.model}")
            return True
        except Exception as e:
            logger.error(f"Failed to update UPS info: {str(e)}")
            return False
    
    def to_dict(self):
        """Convert UPS to dictionary."""
        return {
            'id': self.id,
            'description': self.description,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'battery_type': self.battery_type,
            'serial_number': self.serial_number,
            'firmware': self.firmware,
            'driver': self.driver,
            'polling_interval': self.polling_interval,
            'low_battery_threshold': self.low_battery_threshold,
            'critical_battery_threshold': self.critical_battery_threshold,
            'battery_runtime_threshold': self.battery_runtime_threshold,
            'last_poll': self.last_poll.isoformat() if self.last_poll else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class BatteryHistory(Base):
    """Model for tracking UPS battery status over time."""
    
    __tablename__ = 'battery_history'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50))           # ups.status
    battery_charge = Column(Float)        # battery.charge (%)
    estimated_runtime = Column(Integer)   # battery.runtime (seconds)
    load = Column(Float)                  # ups.load (%)
    input_voltage = Column(Float)         # input.voltage (V)
    output_voltage = Column(Float)        # output.voltage (V)
    
    # Relationships
    ups_id = Column(Integer, ForeignKey('ups.id'))
    ups = relationship("UPS", back_populates="battery_history")
    
    def to_dict(self):
        """Convert battery history entry to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'battery_charge': self.battery_charge,
            'estimated_runtime': self.estimated_runtime,
            'load': self.load,
            'input_voltage': self.input_voltage,
            'output_voltage': self.output_voltage
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