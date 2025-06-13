# Detect and configure UPS
echo "Detecting UPS..."
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
    
    # Capture all UPS information as JSON
    all_info=$(upsc ups 2>/dev/null | awk -F': ' '{gsub(/^[ \t]+|[ \t]+$/, "", $1); gsub(/^[ \t]+|[ \t]+$/, "", $2); printf "\"%s\": \"%s\",\n", $1, $2}' | sed '$ s/,$//')
    all_info="{${all_info}}"
    
    # Log UPS detection
    echo "UPS detected:"
    echo "Manufacturer: ${UPS_MFR:-Unknown Manufacturer}"
    echo "Model: ${UPS_MODEL:-Unknown Model}"
    echo "Battery Type: ${UPS_BATTERY_TYPE:-Unknown}"
    echo "Serial: ${UPS_SERIAL:-Unknown}"
    echo "Firmware: ${UPS_FIRMWARE:-Unknown}"
    echo "Driver: ${UPS_DRIVER:-usbhid-ups}"
    echo "All Info: ${all_info}"
else
    # Default values for no UPS detected
    UPS_MFR="Unknown Manufacturer"
    UPS_MODEL="Unknown Model"
    UPS_BATTERY_TYPE="Unknown"
    UPS_SERIAL=""
    UPS_FIRMWARE="Unknown"
    UPS_DRIVER="usbhid-ups"
    all_info="{}"
    
    # Log no UPS detected
    echo "No UPS detected, using default values"
fi

# Append UPS default configuration to defaults.sql
cat <<EOF >> defaults.sql
INSERT INTO ups (
    manufacturer,
    model,
    battery_type,
    description,
    driver,
    polling_interval,
    all_info
) VALUES (
    '${UPS_MFR:-Unknown Manufacturer}',
    '${UPS_MODEL:-Unknown Model}',
    '${UPS_BATTERY_TYPE:-Unknown}',
    'Auto-detected UPS',
    '${UPS_DRIVER:-usbhid-ups}',
    10,
    '${all_info}'
);
EOF