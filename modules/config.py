from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator, model_validator
from typing import List, Optional, Literal, Dict, Union
import re
import yaml

# Define a webhook channel with optional headers
class WebhookChannel(BaseModel):
    type: Literal["webhook"]
    url: HttpUrl
    headers: Optional[Dict[str, str]] = {}

# Define an email channel with a list of recipients
class EmailChannel(BaseModel):
    type: Literal["email"]
    to: List[EmailStr]

# Union type for a generic channel (webhook or email)
Channel = Union[WebhookChannel, EmailChannel]

# Define an alert rule that uses named channels and optional repeat interval
class AlertRule(BaseModel):
    event: str  # regex pattern to match UPS status events
    methods: List[str]  # list of channel names
    repeat_interval_seconds: Optional[int] = None  # optional repeat timer for persistent alerts

    # Validate that the event string is a valid regular expression
    @field_validator('event')
    def validate_event_regex(cls, v):
        try:
            re.compile(v)
        except re.error:
            raise ValueError(f"Invalid regex pattern: {v}")
        return v

# UPS configuration, including poll interval and NUT status command
class UPSConfig(BaseModel):
    poll_interval_seconds: int = Field(..., gt=0)  # must be > 0
    status_command: str  # typically something like "/bin/upsc ups@localhost"

# Logging configuration, including path and optional JSON output
class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    path: str  # file path for log output
    json_format: bool = False  # true for structured logging

# SMTP server configuration for sending alert emails
class SMTPConfig(BaseModel):
    server: str
    port: int
    username: str
    password: str

# Main configuration schema for the entire application
class PowerSnitchConfig(BaseModel):
    ups: UPSConfig  # UPS settings
    channels: Dict[str, Channel]  # named alert channels
    alerts: List[AlertRule]  # alert rules referencing those channels
    logging: LoggingConfig  # log output behavior
    smtp: SMTPConfig  # email delivery settings

    # Ensure all alert method names refer to defined channels
    @model_validator(mode="after")
    def check_channels_used_in_alerts(self) -> 'PowerSnitchConfig':
        defined_channels = self.channels
        for alert in self.alerts:
            for method in alert.methods:
                if method not in defined_channels:
                    raise ValueError(f"Undefined channel reference in alert: {method}")
        return self

# Load and validate configuration from a YAML file path
def load_config_from_yaml(path: str) -> PowerSnitchConfig:
    with open(path, 'r') as file:
        raw = yaml.safe_load(file)  # parse YAML into a Python dict
    return PowerSnitchConfig(**raw)  # validate and convert into a config object
