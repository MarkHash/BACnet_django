import json
from unittest.mock import Mock, patch

from django.test import Client, RequestFactory
from django.urls import reverse

from discovery.exceptions import ConfigurationError
from discovery.views import (
    _build_device_context,
    _organise_points_by_type,
    _trigger_auto_refresh_if_needed,
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

    @patch("discovery.views._trigger_auto_refresh_if_needed")
    @patch("discovery.views._organise_points_by_type")
    @patch("discovery.views._build_device_context")
    def test_device_detail_calls_helpers(
        self, mock_context, mock_organise, mock_refresh
    ):
        request = self.factory.get(f"/device/{self.device.device_id}/")

        mock_organise.return_value = {"analogInput": [self.analog_point]}
        mock_context.return_value = {"device": self.device}

        response = device_detail(request, self.device.device_id)
        self.assertEqual(response.status_code, 200)

        mock_refresh.assert_called_once()
        mock_organise.assert_called_once()
        mock_context.assert_called_once()

    def test_device_detail_device_not_found(self):
        request = self.factory.get("/device/99999/")

        with self.assertRaises(Exception):
            device_detail(request, 99999)

    def test_device_detail_integration(self):
        request = self.factory.get(f"/device/{self.device.device_id}/")

        with patch("discovery.views._trigger_auto_refresh_if_needed") as mock_refresh:
            response = device_detail(request, self.device.device_id)

            self.assertEqual(response.status_code, 200)
            mock_refresh.assert_called_once()


class TestViewHelperFunctions(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.device = BACnetDeviceFactory(points_read=True)
        self.point = BACnetPointFactory(device=self.device)

    @patch("discovery.views.ensure_bacnet_client")
    @patch("discovery.views._should_refresh_readings")
    def test_trigger_auto_refresh_integration(
        self, mock_should_refresh, mock_ensure_client
    ):
        mock_client = Mock()
        mock_ensure_client.return_value = mock_client
        mock_should_refresh.return_value = True

        points = self.device.points.all()
        _trigger_auto_refresh_if_needed(self.device, points)

        mock_ensure_client.assert_called_once()
        mock_should_refresh.assert_called_once()
        mock_client.read_all_point_values.assert_called_once_with(self.device.device_id)

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
        with patch("discovery.views.ensure_bacnet_client") as mock_ensure:
            mock_client = Mock()
            mock_ensure.return_value = mock_client

            response = self.client.post("/api/start-discovery/")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data["success"])

            mock_client.send_whois.assert_called_once()

    def test_start_discovery_get_invalid(self):
        with patch("discovery.views.ensure_bacnet_client") as mock_ensure:
            mock_client = Mock()
            mock_ensure.return_value = mock_client
            response = self.client.get("/api/start-discovery/")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertFalse(data["success"])
            self.assertEqual(data["message"], "Invalid request")

    def test_read_device_points_success(self):
        with patch("discovery.views.ensure_bacnet_client") as mock_ensure:
            mock_client = Mock()
            mock_ensure.return_value = mock_client

            response = self.client.post(f"/api/read-points/{self.device.device_id}/")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data["success"])
            self.assertIn("Started reading points", data["message"])
            self.assertEqual(data["device_id"], self.device.device_id)

            mock_client.read_device_objects.assert_called_once_with(
                self.device.device_id
            )

    def test_read_point_values_success(self):
        with patch("discovery.views.ensure_bacnet_client") as mock_ensure:
            mock_client = Mock()
            mock_ensure.return_value = mock_client
            response = self.client.post(f"/api/read-values/{self.device.device_id}/")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data["success"])
            self.assertIn("Started reading sensor values", data["message"])

            mock_client.read_all_point_values.assert_called_once_with(
                self.device.device_id
            )


class TestDecoratorIntegration(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.device = BACnetDeviceFactory()

    @patch("discovery.views.ensure_bacnet_client")
    def test_requires_client_only_decorator(self, mock_ensure_client):
        mock_client = Mock()
        mock_ensure_client.return_value = mock_client

        request = self.factory.post("/api/start_discovery/")
        from discovery.views import start_discovery

        response = start_discovery(request)

        self.assertEqual(response.status_code, 200)
        mock_ensure_client.assert_called_once()

    @patch("discovery.views.ensure_bacnet_client")
    def test_requires_device_and_client_decorator(self, mock_ensure_client):
        mock_client = Mock()
        mock_ensure_client.return_value = mock_client

        request = self.factory.post(f"/api/read-points/{self.device.device_id}/")
        from discovery.views import read_device_points

        response = read_device_points(request, self.device.device_id)

        self.assertEqual(response.status_code, 200)
        mock_ensure_client.assert_called_once()


class TestErrorHandling(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    @patch("discovery.views.ensure_bacnet_client")
    def test_configuration_error_handling(self, mock_ensure_client):
        mock_ensure_client.side_effect = ConfigurationError("Config Error")
        request = self.factory.post("/api/start-discovery")

        from discovery.views import start_discovery

        response = start_discovery(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("Configuration error", data["message"])

    def test_device_not_found_in_decorator(self):
        request = self.factory.post("/api/read-points/99999/")

        from discovery.views import read_device_points

        response = read_device_points(request, 99999)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["success"])


class TestViewUtilitiesIntegration(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.device = BACnetDeviceFactory()

    @patch("discovery.views.ensure_bacnet_client")
    def test_ensure_bacnet_client_integration(self, mock_ensure):
        mock_client = Mock()
        mock_ensure.return_value = mock_client

        from discovery.views import ensure_bacnet_client

        result = ensure_bacnet_client()

        self.assertEqual(result, mock_client)
        mock_ensure.assert_called_once()
