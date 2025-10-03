class BACnetConstants:
    # Time and limits
    MAX_READING_LIMIT = 50
    COLLECTION_INTERVAL_SECONDS = 300
    STALE_THRESHOLD_SECONDS = 3600

    # Energy Analytics Constants
    BASE_HVAC_LOAD_KWH = 0.5
    LOAD_PER_DEGREE_KWH = 0.3
    READINGS_PER_HOUR = 3600 / COLLECTION_INTERVAL_SECONDS  # 12 readings per hour
    READINGS_PER_DAY = READINGS_PER_HOUR * 24.0  # 288 readings per day

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

    PERIOD_PARAMETERS = {
        "1hour": 1,
        "6hours": 6,
        "24hours": 24,
        "7days": 7 * 24,
        "30days": 30 * 24,
    }
