"""
Test if device 1000 is discoverable by creating a separate BACnet client
"""

import asyncio

import BAC0


async def test_discover():
    # Create a separate client on different port
    client = BAC0.lite(port=47850)  # No deviceId = pure client

    print("Starting discovery from port 47850...")
    print("Looking for device 1000 on port 47808...")

    await asyncio.sleep(2)  # Wait for client to initialize

    # Discover devices
    devices = client.discover()

    print(f"\nFound {len(devices) if devices else 0} devices:")
    if devices:
        for dev in devices:
            print(f"  - {dev}")

        # Check if device 1000 is in the list
        device_ids = [
            d[1] if isinstance(d, tuple) and len(d) >= 2 else None for d in devices
        ]
        if 1000 in device_ids:
            print("\n✅ SUCCESS: Device 1000 is discoverable!")
        else:
            print("\n❌ Device 1000 NOT found in discovery")
    else:
        print("  (none found)")

    client.disconnect()


asyncio.run(test_discover())
