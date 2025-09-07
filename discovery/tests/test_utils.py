from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from discovery.constants import BACnetConstants
from discovery.views import (
    _build_device_context,
    _organise_points_by_type,
    _should_refresh_readings,
    _trigger_auto_refresh_if_needed,
)

from .test_base import BACnetDeviceFactory, BACnetPointFactory, BaseTestCase


class TestRefreshReadingsLogic(TestCase):
    def test_should_refresh_with_no_reading(self):
        result = _should_refresh_readings(None)
        self.assertTrue(result)

    def test_should_refresh_with_fresh_data(self):
        fresh_reading = Mock()
        fresh_reading.value_last_read = timezone.now() - timedelta(minutes=2)

        result = _should_refresh_readings(fresh_reading)
        self.assertFalse(result)

    def test_should_refresh_with_stale_data(self):
        stale_reading = Mock()
        stale_reading.value_last_read = timezone.now() - timedelta(minutes=10)

        result = _should_refresh_readings(stale_reading)
        self.assertTrue(result)

    def test_should_refresh_at_exact_threshold(self):
        threshold_reading = Mock()
        threshold_reading.value_last_read = timezone.now() - timedelta(
            seconds=BACnetConstants.REFRESH_THRESHOLD_SECONDS
        )

        result = _should_refresh_readings(threshold_reading)
        self.assertTrue(result)


class TestOrganisePointsByType(BaseTestCase):
    def test_organise_empty_points(self):
        # from django.db.models import QuerySet

        empty_points = self.device.points.none()

        result = _organise_points_by_type(empty_points)
        assert result == {}

    def test_organise_single_point(self):
        points = self.device.points.all()
        result = _organise_points_by_type(points)

        self.assertEqual(len(result), 1)
        self.assertIn("analogInput", result)
        self.assertEqual(len(result["analogInput"]), 1)
        self.assertEqual(result["analogInput"][0], self.point)

    def test_organise_multiple_point_types(self):
        analog_input = BACnetPointFactory(
            device=self.device, object_type="analogInput", instance_number=1
        )
        analog_output = BACnetPointFactory(
            device=self.device, object_type="analogOutput", instance_number=2
        )
        binary_input = BACnetPointFactory(
            device=self.device, object_type="binaryInput", instance_number=3
        )
        another_analog_input = BACnetPointFactory(
            device=self.device, object_type="analogInput", instance_number=4
        )

        points = [analog_input, analog_output, binary_input, another_analog_input]
        result = _organise_points_by_type(points)

        self.assertEqual(len(result), 3)
        self.assertIn("analogInput", result)
        self.assertIn("analogOutput", result)
        self.assertIn("binaryInput", result)

        self.assertEqual(len(result["analogInput"]), 2)
        self.assertEqual(len(result["analogOutput"]), 1)
        self.assertEqual(len(result["binaryInput"]), 1)


class TestBuildDeviceContext(BaseTestCase):
    def test_build_context_with_data(self):
        points = self.device.points.all()
        points_by_type = {"analogInput": [self.point]}
        result = _build_device_context(self.device, points, points_by_type)

        expected_keys = [
            "device",
            "points",
            "points_by_type",
            "point_count",
            "points_loaded_recently",
        ]
        assert all(key in result for key in expected_keys)

        self.assertEqual(result["device"], self.device)
        self.assertEqual(result["points"], points)
        self.assertEqual(result["points_by_type"], points_by_type)
        self.assertEqual(result["point_count"], len(points))
        self.assertTrue(result["points_loaded_recently"])

    def test_build_context_no_points_loaded(self):
        device_no_points = BACnetDeviceFactory(points_read=False)
        points = device_no_points.points.none()
        points_by_type = {}

        result = _build_device_context(device_no_points, points, points_by_type)

        self.assertFalse(result["points_loaded_recently"])
        self.assertEqual(result["point_count"], 0)


class TestTriggerAutoRefreshIntegration(BaseTestCase):
    @patch("discovery.views.ensure_bacnet_client")
    @patch("discovery.views._should_refresh_readings")
    def test_trigger_auto_refresh_success(
        self, mock_should_refresh, mock_ensure_client
    ):
        mock_client = Mock()
        mock_ensure_client.return_value = mock_client
        mock_should_refresh.return_value = True

        # self.device.points_read = True
        # self.device.save()

        points = self.device.points.all()

        _trigger_auto_refresh_if_needed(self.device, points)

        mock_ensure_client.assert_called_once()
        mock_should_refresh.assert_called_once()
        mock_client.read_all_point_values.assert_called_once_with(self.device.device_id)

    @patch("discovery.views.ensure_bacnet_client")
    def test_trigger_auto_refresh_no_points(self, mock_ensure_client):
        device_no_points = BACnetDeviceFactory()
        empty_points = device_no_points.points.none()

        _trigger_auto_refresh_if_needed(device_no_points, empty_points)

        mock_ensure_client.assert_not_called()

    @patch("discovery.views.ensure_bacnet_client")
    def test_trigger_auto_refresh_points_not_read(self, mock_ensure_client):
        device_not_read = BACnetDeviceFactory(points_read=False)
        points = device_not_read.points.all()

        _trigger_auto_refresh_if_needed(device_not_read, points)

        mock_ensure_client.assert_not_called()
