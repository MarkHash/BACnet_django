import BAC0

try:
    bacnet = BAC0.connect()

    print("Testing correct readMultiple format...")

    # Correct format: single string with multiple properties from same object
    try:
        print("Test: Reading multiple properties from same object...")
        result = bacnet.readMultiple(
            "192.168.1.232 analogValue 1201004 presentValue units"
        )
        print(f"✅ Single object, multiple properties: {result}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test: Multiple objects (if supported)
    try:
        print("\nTest: Multiple objects in one call...")
        result = bacnet.readMultiple(
            "192.168.1.232 analogValue 1201004 presentValue analogValue "
            "1201005 presentValue"
        )
        print(f"✅ Multiple objects: {result}")
    except Exception as e:
        print(f"❌ Multiple objects failed: {e}")

    bacnet.disconnect()

except Exception as e:
    print(f"Connection error: {e}")
