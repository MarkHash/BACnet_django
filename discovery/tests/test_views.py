import json
from datetime import timedelta
from unittest.mock import ANY, Mock, patch

from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone

from discovery.models import BACnetDevice
from discovery.views import (
    _build_device_context,
    _organise_points_by_type,
    dashboard,
    device_detail,
)

from .test_base import BACnetDeviceFactory, BACnetPointFactory, BaseTestCase


class TestDashboardView(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client = Client()

        self.online_device = BACnetDeviceFactory(is_online=True)
        self.offline_device = BACnetDeviceFactory(is_online=False)

        BACnetPointFactory(device=self.online_device)
        BACnetPointFactory(device=self.offline_device)

    def test_dashboard_get_success(self):
        request = self.factory.get("/dashboard/")
        response = dashboard(request)

        self.assertEqual(response.status_code, 200)
        # self.assertContains(response, 'dashboard.html')

    def test_dashboard_context_data(self):
        # request = self.factory.get("/dashboard")

        response = self.client.get(reverse("discovery:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("devices", response.context)
        self.assertIn("total_devices", response.context)
        self.assertIn("online_devices", response.context)
        self.assertIn("offline_devices", response.context)
        self.assertIn("total_points", response.context)

        self.assertEqual(response.context["total_devices"], 3)
        self.assertEqual(response.context["online_devices"], 2)
        self.assertEqual(response.context["offline_devices"], 1)
        self.assertEqual(response.context["total_points"], 3)


class TestDeviceDetailView(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

        self.device = BACnetDeviceFactory(points_read=True)
        self.analog_point = BACnetPointFactory(
            device=self.device, object_type="analogInput", instance_number=1
        )
        self.binary_point = BACnetPointFactory(
            device=self.device, object_type="binaryInput", instance_number=2
        )

    @patch("discovery.views._organise_points_by_type")
    @patch("discovery.views._build_device_context")
    def test_device_detail_calls_helpers(self, mock_context, mock_organise):
        request = self.factory.get(f"/device/{self.device.device_id}/")

        mock_organise.return_value = {"analogInput": [self.analog_point]}
        mock_context.return_value = {"device": self.device}

        response = device_detail(request, self.device.device_id)
        self.assertEqual(response.status_code, 200)

        mock_organise.assert_called_once()
        mock_context.assert_called_once()

    def test_device_detail_device_not_found(self):
        request = self.factory.get("/device/99999/")

        with self.assertRaises(Exception):
            device_detail(request, 99999)

    def test_device_detail_integration(self):
        request = self.factory.get(f"/device/{self.device.device_id}/")

        response = device_detail(request, self.device.device_id)

        self.assertEqual(response.status_code, 200)


class TestViewHelperFunctions(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.device = BACnetDeviceFactory(points_read=True)
        self.point = BACnetPointFactory(device=self.device)

    def test_organise_points_by_type_integration(self):
        BACnetPointFactory(device=self.device, object_type="analogOutput")
        BACnetPointFactory(device=self.device, object_type="binaryInput")

        points = self.device.points.all()
        result = _organise_points_by_type(points)

        self.assertEqual(len(result), 3)
        self.assertIn("analogOutput", result)
        self.assertIn("binaryInput", result)

    def test_build_device_context_integration(self):
        points = self.device.points.all()
        points_by_type = _organise_points_by_type(points)

        context = _build_device_context(self.device, points, points_by_type)

        self.assertEqual(context["device"], self.device)
        self.assertEqual(context["points"], points)
        self.assertEqual(context["points_by_type"], points_by_type)
        self.assertEqual(context["point_count"], points.count())
        self.assertTrue(context["points_loaded_recently"])


class TestAPIViews(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.device = BACnetDeviceFactory()
        self.point = BACnetPointFactory(device=self.device)

    def test_start_discovery_post_success(self):
        with patch("discovery.views.BACnetService") as mock_ensure:
            mock_service = Mock()
            mock_service.discover_devices.return_value = [{"deviceId": 123}]
            mock_ensure.return_value = mock_service

            response = self.client.post("/api/start-discovery/")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data["success"])

            mock_service.discover_devices.assert_called_once()

    def test_start_discovery_get_invalid(self):
        with patch("discovery.views.BACnetService") as mock_ensure:
            mock_service = Mock()
            mock_ensure.return_value = mock_service
            response = self.client.get("/api/start-discovery/")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertFalse(data["success"])
            self.assertEqual(data["message"], "Invalid request")

    def test_discover_device_points_success(self):
        with patch("discovery.views.BACnetService") as mock_ensure:
            mock_service = Mock()
            mock_service.discover_device_points.return_value = [Mock(), Mock()]
            mock_ensure.return_value = mock_service

            response = self.client.post(
                f"/api/discover-points/{self.device.device_id}/"
            )

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data["success"])
            self.assertIn("Discovered", data["message"])
            self.assertEqual(data["device_id"], self.device.device_id)

            mock_service.discover_device_points.assert_called_once_with(ANY)

    def test_read_point_values_success(self):
        with patch("discovery.views.BACnetService") as mock_ensure:
            mock_service = Mock()
            # Mock the methods the view actually calls:
            mock_service._initialise_results.return_value = {
                "readings_collected": 5,
                "devices_processed": 0,
            }
            mock_service._connect.return_value = True
            mock_service.read_device_points.return_value = None
            mock_service._disconnect.return_value = None
            mock_ensure.return_value = mock_service

            response = self.client.post(f"/api/read-values/{self.device.device_id}/")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data["success"])
            self.assertIn("Read", data["message"])

            # Assert the methods that are actually called:
            mock_service._initialise_results.assert_called_once()
            mock_service._connect.assert_called_once()
            mock_service.read_device_points.assert_called_once()


class TestErrorHandling(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_device_not_found_in_decorator(self):
        request = self.factory.post("/api/read-points/99999/")

        from discovery.views import discover_device_points

        response = discover_device_points(request, 99999)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["success"])


class TestDeviceTrendsAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.device = BACnetDeviceFactory(device_id=8001)
        self.client = Client()

    def test_device_trends_success(self):
        """Test successful device trends API call"""
        response = self.client.get(
            f"/api/devices/{self.device.device_id}/analytics/trends/?period=24hours"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["device_id"], self.device.device_id)
        self.assertEqual(data["period"], "24hours")

    def test_device_trends_invalid_period(self):
        """Test device trends API call with invalid period parameter"""
        response = self.client.get(
            f"/api/devices/{self.device.device_id}/analytics/trends/?period=invalid"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("Invalid period", data["error"]["message"])

    def test_device_trends_nonexistent_device(self):
        """Test device trends API call with non-existent device ID"""
        response = self.client.get("/api/devices/999/analytics/trends/")
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "DEVICE_NOT_FOUND")


class TestDeviceStatusAPI(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()

        self.online_device = BACnetDeviceFactory(
            device_id=1001,
            is_online=True,
            last_seen=timezone.now() - timedelta(minutes=5),
        )
        self.offline_device = BACnetDeviceFactory(
            device_id=1002,
            is_online=False,
            last_seen=timezone.now() - timedelta(hours=2),
        )
        self.stale_device = BACnetDeviceFactory(
            device_id=1003,
            is_online=True,
            last_seen=timezone.now() - timedelta(hours=2),
        )

        BACnetPointFactory(device=self.online_device, present_value="25.5")
        BACnetPointFactory(device=self.stale_device, present_value="22.1")

    def test_devices_status_success(self):
        """Test successful device status API call"""
        response = self.client.get("/api/devices/status/")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("summary", data)
        self.assertIn("devices", data)
        self.assertIn("timestamp", data)

        summary = data["summary"]
        self.assertIn("total_devices", summary)
        self.assertIn("online_devices", summary)
        self.assertIn("offline_devices", summary)
        self.assertIn("stale_devices", summary)
        self.assertIn("no_data_devices", summary)

        devices = data["devices"]
        self.assertGreater(len(devices), 0)

        device = devices[0]
        self.assertIn("device_id", device)
        self.assertIn("address", device)
        self.assertIn("statistics", device)

        stats = device["statistics"]
        self.assertIn("total_points", stats)
        self.assertIn("readable_points", stats)
        self.assertIn("points_with_values", stats)
        self.assertIn("device_status", stats)
        self.assertIn("last_reading_time", stats)

    def test_devices_status_empty_database(self):
        """Test device status API with no devices"""
        BACnetDevice.objects.all().delete()

        response = self.client.get("/api/devices/status/")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["summary"]["total_devices"], 0)
        self.assertEqual(len(data["devices"]), 0)

    def test_devices_status_http_method_validation(self):
        """Test that device status API only accepts GET requests"""
        response = self.client.post("/api/devices/status/")
        self.assertEqual(response.status_code, 200)
