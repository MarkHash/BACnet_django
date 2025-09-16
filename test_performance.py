import time

import BAC0


def test_performance():
    try:
        bacnet = BAC0.connect()
        device_address = "192.168.1.232"

        # Define 28 points to test (adjust based on your actual points)
        test_points = []
        for i in range(1201004, 1201012):  # analogValue points
            test_points.append(f"analogValue {i}")
        for i in range(1203001, 1203021):  # analogInput points
            test_points.append(f"analogInput {i}")

        print(f"Testing performance with {len(test_points)} points on {device_address}")
        print("=" * 60)

        # Test 1: Individual reads (current method)
        print("Test 1: Individual reads...")
        start_time = time.time()
        individual_results = []
        individual_success = 0

        for point in test_points:
            try:
                read_string = f"{device_address} {point} presentValue"
                result = bacnet.read(read_string)
                individual_results.append(result)
                individual_success += 1
            except Exception as e:
                individual_results.append(f"ERROR: {e}")

        individual_time = time.time() - start_time
        print(f"  ✅ Completed in {individual_time:.2f} seconds")
        print(
            f"  📊 Success rate: {individual_success}/{len(test_points)} "
            f"({individual_success/len(test_points)*100:.1f}%)"
        )

        # Test 2: Batch read (new method)
        print("\nTest 2: Batch read...")
        start_time = time.time()

        try:
            batch_parts = [device_address]
            for point in test_points:
                parts = point.split()  # ["analogValue", "1201004"]
                batch_parts.extend([parts[0], parts[1], "presentValue"])

            batch_request = " ".join(batch_parts)
            print(f"  📦 Batch request length: {len(batch_request)} characters")

            batch_results = bacnet.readMultiple(batch_request)
            batch_time = time.time() - start_time

            print(f"  ✅ Completed in {batch_time:.2f} seconds")
            print(
                f"  📊 Results: {len(batch_results) if batch_results else 0} "
                f"values returned"
            )

            # Performance comparison
            if individual_time > 0 and batch_time > 0:
                speedup = individual_time / batch_time
                print("\n🚀 PERFORMANCE IMPROVEMENT:")
                print(f"  Individual reads: {individual_time:.2f}s")
                print(f"  Batch read: {batch_time:.2f}s")
                print(f"  Speedup: {speedup:.1f}x faster")
                print(
                    f"  Time saved: {individual_time - batch_time:.2f}s "
                    f"({(1-batch_time/individual_time)*100:.1f}% faster)"
                )

        except Exception as e:
            batch_time = time.time() - start_time
            print(f"  ❌ Batch read failed after {batch_time:.2f}s: {e}")
            batch_results = None

        # Show sample results
        print("\n📋 SAMPLE RESULTS:")
        print("Individual reads (first 5):")
        for i, result in enumerate(individual_results[:5]):
            print(f"  {test_points[i]}: {result}")

        if batch_results:
            print("Batch read (first 5):")
            for i, result in enumerate(batch_results[:5]):
                print(f"  {test_points[i]}: {result}")

        bacnet.disconnect()

    except Exception as e:
        print(f"Connection error: {e}")


if __name__ == "__main__":
    test_performance()
