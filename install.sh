# Detect and configure UPS
if lsusb | grep -qi "UPS"; then
    # UPS detected, get info from NUT
    systemctl start nut-server
    sleep 2
    
    # Get UPS information from NUT
    UPS_MFR=$(upsc ups 2>/dev/null | grep "device.mfr" | cut -d: -f2 | xargs)
    UPS_MODEL=$(upsc ups 2>/dev/null | grep "device.model" | cut -d: -f2 | xargs)
    UPS_BATTERY_TYPE=$(upsc ups 2>/dev/null | grep "battery.type" | cut -d: -f2 | xargs)
    UPS_SERIAL=$(upsc ups 2>/dev/null | grep "ups.serial" | cut -d: -f2 | xargs)
    UPS_FIRMWARE=$(upsc ups 2>/dev/null | grep "ups.firmware" | cut -d: -f2 | xargs)
    UPS_DRIVER=$(upsc ups 2>/dev/null | grep "driver.name" | cut -d: -f2 | xargs)
    
    # Log UPS detection
    echo "UPS detected:"
    echo "Manufacturer: ${UPS_MFR:-Unknown Manufacturer}"
    echo "Model: ${UPS_MODEL:-Unknown Model}"
    echo "Battery Type: ${UPS_BATTERY_TYPE:-Unknown}"
    echo "Serial: ${UPS_SERIAL:-Unknown}"
    echo "Firmware: ${UPS_FIRMWARE:-Unknown}"
    echo "Driver: ${UPS_DRIVER:-usbhid-ups}"
else
    # Default values for no UPS detected
    UPS_MFR="Unknown Manufacturer"
    UPS_MODEL="Unknown Model"
    UPS_BATTERY_TYPE="Unknown"
    UPS_SERIAL=""
    UPS_FIRMWARE="Unknown"
    UPS_DRIVER="usbhid-ups"
    
    # Log no UPS detected
    echo "No UPS detected, using default values"
fi

# Export variables for use in defaults.sql
export UPS_MFR UPS_MODEL UPS_BATTERY_TYPE UPS_SERIAL UPS_FIRMWARE UPS_DRIVER 