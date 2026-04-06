# Power Snitch

This project is a simple and elegant monitor and alerting agent for USB connected UPS systems. Runnning under the Linux operating system. The system is light weight enough to run on a raspberry pi ZeroW to monitor a single UPS to on a mini-pc to monitor many UPS systems. 

# Basic Features
- Runs under systemd
- simple but elegant UI for configiuration
- monitors UPS systems connected via USB for a defined set of conditions 
- each condition for each UPS can be configured to generate a notification alert via a notification channel


## Stack
- Python
- Nut (linux UPS Monitor)
- Fast API
- sqllite for configuration data
- iunfluxdb for time-series data
- Bootstrap CSS libs for interface

## Conditions Monitored and recorded

These are the initial conditions which are monitored

- on_battery	OB	UPS is running on battery (power outage)
- on_line	OL	Utility power is online
- low_battery	LB	Battery charge is critically low
- replace_battery	RB	Battery needs to be replaced
- overload	OVER	UPS load is too high
- shutdown_imminent	FSD	Forced shutdown has been initiated
- battery_low_pct	battery.charge < USER_DEFINED
- runtime_low	battery.runtime < USER_DEFINED

## Notification Services
- Telegram
    - Bot configured at the service level
    - user to send the message to configured on the channel level
- SMS
    - sms is designed to function with Twillo user the webhook method
    - sms service configured on the service level 
    - destination of message is configured on the channel level
- Webhook
    - all configuration on the channel level 
- Email
    - relay server credentials configured at service level
    - message destination at channel level

## Notification Channels
Channels are a User defined and named instance of a Notification service configuration. 
- Each condition which generates an alert has a clear and simple default message.
    - UPS name/ID 
    - Condition met
    - Condition Value
- Users may add additional information to the default message when defining a channel


# Python 
The python code for the application is pyblished to PyPi.org as a module via git workflows. 

# Installation
Installation is completed via a shell script which:
- ensures OS requirements are net
    - installs missing moduels
- installs the python modules
- creates and enables systemd unit
- completes with a user message on how to connect and configure. 

# Configuration
Configuration is done via Web UI

# Web UI 
- Shows discovered UPS systems on USB Bus
- allows enable or disable of monitoring
- configures notification channels generally
- configures UPS condition to Notification Channel mapping

# Auth and security
This is a single user system with a user name `admin` and password 
- default password is randomly generated on install and user changable via web ui.