"""
BACnet Object Templates for Virtual Device Creation

This module defines standardized object configurations for different types
of virtual BACnet devices. Each template includes appropriate objects
with realistic properties for building automation scenarios.
"""

BACNET_OBJECT_TEMPLATES = {
    "temperature_sensor": {
        "description": "Temperature and humidity monitoring device",
        "objects": [
            {
                "type": "analogInput",
                "name": "Temperature",
                "description": "Room temperature reading",
                "units": "degreesCelsius",
                "default_value": 22.0,
                "min_value": -10.0,
                "max_value": 50.0,
            },
            {
                "type": "analogInput",
                "name": "Humidity",
                "description": "Relative humidity reading",
                "units": "percent",
                "default_value": 45.0,
                "min_value": 0.0,
                "max_value": 100.0,
            },
            {
                "type": "analogInput",
                "name": "Status",
                "description": "Device operational status",
                "units": "noUnits",
                "default_value": 1.0,
                "min_value": 0.0,
                "max_value": 1.0,
            },
        ],
    },
    "hvac_controller": {
        "description": "HVAC system controller with setpoints and fan control",
        "objects": [
            {
                "type": "analogOutput",
                "name": "Temperature_Setpoint",
                "description": "Temperature setpoint control",
                "units": "degreesCelsius",
                "default_value": 24.0,
                "min_value": 18.0,
                "max_value": 28.0,
                "writable": True,
            },
            {
                "type": "binaryOutput",
                "name": "Fan_Control",
                "description": "Fan on/off control",
                "default_value": 0,
                "active_text": "On",
                "inactive_text": "Off",
                "writable": True,
            },
            {
                "type": "analogInput",
                "name": "Current_Temperature",
                "description": "Current room temperature",
                "units": "degreesCelsius",
                "default_value": 23.0,
                "min_value": 15.0,
                "max_value": 35.0,
            },
            {
                "type": "binaryInput",
                "name": "Occupancy_Sensor",
                "description": "Room occupancy detection",
                "default_value": 0,
                "active_text": "Occupied",
                "inactive_text": "Vacant",
            },
        ],
    },
    "lighting_controller": {
        "description": "Lighting control panel with dimming capabilities",
        "objects": [
            {
                "type": "binaryOutput",
                "name": "Light_Switch",
                "description": "Main lighting control",
                "default_value": 0,
                "active_text": "On",
                "inactive_text": "Off",
                "writable": True,
            },
            {
                "type": "analogOutput",
                "name": "Dimmer_Level",
                "description": "Light dimming level",
                "units": "percent",
                "default_value": 80.0,
                "min_value": 0.0,
                "max_value": 100.0,
                "writable": True,
            },
            {
                "type": "analogInput",
                "name": "Light_Sensor",
                "description": "Ambient light level",
                "units": "percent",
                "default_value": 50.0,
                "min_value": 0.0,
                "max_value": 100.0,
            },
        ],
    },
    "energy_meter": {
        "description": "Electrical energy monitoring device",
        "objects": [
            {
                "type": "analogInput",
                "name": "Power_Consumption",
                "description": "Current power consumption",
                "units": "kilowatts",
                "default_value": 2.5,
                "min_value": 0.0,
                "max_value": 100.0,
            },
            {
                "type": "analogInput",
                "name": "Energy_Total",
                "description": "Total energy consumed",
                "units": "kilowattHours",
                "default_value": 1234.5,
                "min_value": 0.0,
                "max_value": 999999.0,
            },
            {
                "type": "analogInput",
                "name": "Voltage",
                "description": "Line voltage measurement",
                "units": "volts",
                "default_value": 120.0,
                "min_value": 100.0,
                "max_value": 140.0,
            },
            {
                "type": "analogInput",
                "name": "Current",
                "description": "Line current measurement",
                "units": "amperes",
                "default_value": 10.5,
                "min_value": 0.0,
                "max_value": 50.0,
            },
        ],
    },
    "generic_device": {
        "description": "Generic BACnet device with basic monitoring",
        "objects": [
            {
                "type": "analogInput",
                "name": "Status",
                "description": "Device operational status",
                "units": "noUnits",
                "default_value": 1.0,
                "min_value": 0.0,
                "max_value": 1.0,
            },
            {
                "type": "binaryInput",
                "name": "Alarm",
                "description": "General alarm status",
                "default_value": 0,
                "active_text": "Alarm",
                "inactive_text": "Normal",
            },
        ],
    },
}

# Object type mappings for BAC0 integration
BACNET_OBJECT_TYPE_MAP = {
    "analogInput": "AI",
    "analogOutput": "AO",
    "binaryInput": "BI",
    "binaryOutput": "BO",
}

# Default device properties
DEFAULT_DEVICE_PROPERTIES = {
    "vendor_id": 999,
    "vendor_name": "Django BACnet Virtual",
    "model_name": "Virtual Device",
    "firmware_revision": "1.0",
    "application_software_version": "1.0",
    "protocol_version": 1,
    "protocol_revision": 22,
}


def get_device_template(device_name):
    """
    Determine appropriate template based on device name.

    Args:
        device_name (str): Name of the virtual device

    Returns:
        str: Template key for BACNET_OBJECT_TEMPLATES
    """
    device_name_lower = device_name.lower()

    temp_keywords = ["temp", "temperature", "sensor"]
    if any(keyword in device_name_lower for keyword in temp_keywords):
        return "temperature_sensor"
    elif any(keyword in device_name_lower for keyword in ["hvac", "air", "climate"]):
        return "hvac_controller"
    elif any(keyword in device_name_lower for keyword in ["light", "lighting", "lamp"]):
        return "lighting_controller"
    elif any(
        keyword in device_name_lower
        for keyword in ["energy", "meter", "power", "electric"]
    ):
        return "energy_meter"
    else:
        return "generic_device"


def get_template_objects(template_key):
    """
    Get object configuration for a specific template.

    Args:
        template_key (str): Template key from BACNET_OBJECT_TEMPLATES

    Returns:
        list: List of object configurations
    """
    if template_key not in BACNET_OBJECT_TEMPLATES:
        template_key = "generic_device"

    return BACNET_OBJECT_TEMPLATES[template_key]["objects"]


def create_bac0_object_args(obj_template):
    """
    Create BAC0 factory arguments from template.

    Args:
        obj_template (dict): Object template configuration

    Returns:
        tuple: (name, description, properties) for BAC0 factory functions
    """
    name = obj_template["name"]
    description = obj_template["description"]
    properties = {}

    # Add type-specific properties
    if obj_template["type"] in ["analogInput", "analogOutput"]:
        properties["units"] = obj_template["units"]
        if "default_value" in obj_template:
            properties["presentValue"] = obj_template["default_value"]

    elif obj_template["type"] in ["binaryInput", "binaryOutput"]:
        if "default_value" in obj_template:
            properties["presentValue"] = obj_template["default_value"]
        if "active_text" in obj_template:
            properties["activeText"] = obj_template["active_text"]
        if "inactive_text" in obj_template:
            properties["inactiveText"] = obj_template["inactive_text"]

    return name, description, properties


def get_object_factory_function(obj_type):
    """
    Get the appropriate BAC0 factory function for object type.

    Args:
        obj_type (str): Object type (analogInput, binaryOutput, etc.)

    Returns:
        function: BAC0 factory function
    """
    try:
        from BAC0.core.devices.local.factory import (
            analog_input,
            analog_output,
            binary_input,
            binary_output,
        )

        factory_map = {
            "analogInput": analog_input,
            "analogOutput": analog_output,
            "binaryInput": binary_input,
            "binaryOutput": binary_output,
        }

        return factory_map.get(obj_type)
    except ImportError:
        return None
