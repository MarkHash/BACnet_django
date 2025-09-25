#!/usr/bin/env python3
import socket

print("Testing network access from subprocess...")

# Test 192.168.1.5:47808
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("192.168.1.5", 47808))
    s.close()
    print("✅ 192.168.1.5:47808 bind successful - IP is accessible")
except Exception as e:
    print(f"❌ 192.168.1.5:47808 bind failed: {e}")

# Test 192.168.1.5:47809
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("192.168.1.5", 47809))
    s.close()
    print("✅ 192.168.1.5:47809 bind successful")
except Exception as e:
    print(f"❌ 192.168.1.5:47809 bind failed: {e}")

print("Test complete")
