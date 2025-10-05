#!/usr/bin/env python
"""
Find actual date ranges with BACnet data in the database
"""

import os
from datetime import datetime, timedelta

import django
from django.db.models import Count, Max, Min

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.settings")
django.setup()

from discovery.models import BACnetReading  # noqa: E402


def find_data_dates():
    """Find what date ranges actually have temperature data."""

    print("📊 Overall BACnet Readings Analysis")
    print("=" * 50)

    # Overall date range
    total_readings = BACnetReading.objects.count()
    print(f"Total BACnet readings in database: {total_readings:,}")

    if total_readings == 0:
        print("❌ No BACnet readings found in database!")
        return

    # Get overall date range
    date_range = BACnetReading.objects.aggregate(
        earliest=Min("read_time"), latest=Max("read_time"), total_count=Count("id")
    )

    print("\n📅 Overall BACnet Readings Date Range:")
    print(f"   Earliest: {date_range['earliest']}")
    print(f"   Latest: {date_range['latest']}")
    print(f"   Total readings: {date_range['total_count']:,}")

    # Get date range for temperature readings specifically
    temp_date_range = (
        BACnetReading.objects.filter(point__units__icontains="degree")
        .exclude(value="0.0")
        .aggregate(
            earliest=Min("read_time"), latest=Max("read_time"), total_count=Count("id")
        )
    )

    print("\n🌡️  Temperature Sensor Data Analysis")
    print(f"   Temperature readings: {temp_date_range['total_count']:,}")
    print(f"   Earliest temp: {temp_date_range['earliest']}")
    print(f"   Latest temp: {temp_date_range['latest']}")

    # Find days with significant data
    if temp_date_range["earliest"]:
        start_date = temp_date_range["earliest"].date()
        end_date = temp_date_range["latest"].date()
        current_date = start_date

        print("\n📈 Daily Reading Volume Analysis")
        print("Days with temperature readings:")

        significant_days = []
        while current_date <= end_date:
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = day_start + timedelta(days=1)

            daily_count = (
                BACnetReading.objects.filter(
                    point__units__icontains="degree",
                    read_time__gte=day_start,
                    read_time__lt=day_end,
                )
                .exclude(value="0.0")
                .count()
            )

            if daily_count > 50:  # Significant data
                date_str = current_date.strftime("%Y-%m-%d")
                print(f"  📅 {date_str}: {daily_count} readings")
                significant_days.append((current_date, daily_count))

            current_date += timedelta(days=1)

        # Recommendations
        if significant_days:
            best_day = max(significant_days, key=lambda x: x[1])
            print("\n🎯 Recommendations for anomaly testing:")
            print(
                f"   Best day for testing: {best_day[0]} " f"({best_day[1]} readings)"
            )
            print(
                f"   Use timeframe: {best_day[0]} to "
                f"{best_day[0] + timedelta(days=1)}"
            )


if __name__ == "__main__":
    find_data_dates()
