class BACnetConstants:
    # Time and limits
    MAX_READING_LIMIT = 50
    REFRESH_THRESHOLD_SECONDS = 300

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

    UNIT_CONVERSIONS = {
        "percent": "%",
        "degreesCelsius": "°C",
        "degreesFahrenheit": "°F",
        "degreesKelvin": "K",
        "volts": "V",
        "amperes": "A",
        "kilowatts": "kW",
        "kilowattHours": "kWh",
        "noUnits": "",
        "litersPerSecond": "L/s",
        "cubicMetersPerSecond": "m³/s",
        "poundsMass": "lbs",
        "kilograms": "kg",
        "metersPerSecond": "m/s",
    }
