class BACnetConstants:
    # Time and limits
    MAX_READING_LIMIT = 50
    REFRESH_THRESHOLD_SECONDS = 300

    # BACnet Property Names
    VENDOR_IDENTIFIER = "vendorIdentifier"
    OBJECT_LIST = "objectList"
    PRESENT_VALUE = "presentValue"
    OBJECT_NAME = "objectName"
    UNITS = "units"

    # BACnet readable object types
    READABLE_OBJECT_TYPES = [
        "analogInput",
        "analogOutput",
        "analogValue",
        "binaryInput",
        "binaryOutput",
        "binaryValue",
        "multiStateInput",
        "multiStateOutput",
        "multiStateValue",
    ]

    # Object Types with Units
    ANALOG_OBJECT_TYPES = [
        "analogInput",
        "analogOutput",
        "analogValue",
    ]

    UNIT_CONVERSIONS = {
        "percent": "%",
        "percentRelativeHumidity": "% RH",
        "degreesCelsius": "°C",
        "degreesFahrenheit": "°F",
        "degreesKelvin": "K",
        "deltaDegreesKelvin": "ΔK",
        "volts": "V",
        "amperes": "A",
        "kilowatts": "kW",
        "kilowattHours": "kWh",
        "megawattHours": "MWh",
        "noUnits": "",
        "litersPerSecond": "L/s",
        "cubicMeters": "m³",
        "cubicMetersPerSecond": "m³/s",
        "cubicMetersPerHour": "m³/h",
        "squareMeters": "m²",
        "poundsMass": "lbs",
        "kilograms": "kg",
        "metersPerSecond": "m/s",
    }
