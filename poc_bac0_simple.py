"""
BAC0 Virtual Device - Simple POC for MVP

This minimal POC validates that:
1. BAC0.lite() creates a discoverable BACnet device
2. Custom device ID can be specified
3. Device responds to WhoIs requests
4. Other BACnet tools can discover it

Usage:
    python poc_bac0_simple.py

Testing:
    1. Run this script
    2. Use Yabe or BACnet browser
    3. Perform WhoIs scan
    4. Look for Device ID 999
"""

import time

import BAC0


def main():
    print("=" * 60)
    print("BAC0 Virtual Device - Simple POC")
    print("=" * 60)

    # Step 1: Create virtual BACnet device
    print("\n[1] Creating virtual BACnet device...")
    print("  Device ID: 999")
    print("  Port: 47808 (standard BACnet port)")

    try:
        # Create BAC0 instance with custom device ID
        # This becomes a discoverable BACnet device!
        bacnet = BAC0.lite(deviceId=999)

        print("\n✓ Success! Virtual device created")
        print(
            f"  Device Object: {bacnet.this_application.localDevice.objectIdentifier}"
        )
        print(f"  IP Address: {bacnet.localIPAddr}")
        print(f"  Device Name: {bacnet.this_application.localDevice.objectName}")

    except Exception as e:
        print(f"\n✗ Failed: {e}")
        print("\nPossible issues:")
        print("  - Port 47808 already in use")
        print("  - Network interface not configured")
        print("  - Try: BAC0.lite(ip='YOUR_IP/24', deviceId=999)")
        return

    # Step 2: Display instructions
    print("\n" + "=" * 60)
    print("TESTING INSTRUCTIONS")
    print("=" * 60)
    print(
        """
1. While this script is running, open a BACnet browser:
   - Yabe (Yet Another BACnet Explorer)
   - Any BACnet discovery tool

2. Perform a WhoIs scan on your network

3. You should see:
   - Device ID: 999
   - IP: Your machine's IP

4. Try reading device properties from the browser

5. Press Ctrl+C here to stop the virtual device
    """
    )
    print("=" * 60)

    # Keep running
    try:
        print("\n[Server Running] Press Ctrl+C to stop...\n")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n[Shutting Down]")
        bacnet.disconnect()
        print("✓ Virtual device stopped")
        print("\n✓ POC Complete!")

        print("\nNext Steps:")
        print("1. If device was discoverable → Proceed with Django integration")
        print("2. If issues → Check network config and troubleshoot")


if __name__ == "__main__":
    main()
