import json
from unittest.mock import Mock, patch

from django.test import Client
from django.urls import reverse

from discovery.models import BACnetDevice

from .test_base import BACnetDeviceFactory, BACnetPointFactory, BaseTestCase


class TestDashboardIntegration(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()

        self.online_device = BACnetDeviceFactory(is_online=True, points_read=True)
        self.offline_device = BACnetDeviceFactory(is_online=False, points_read=False)

        for _ in range(3):
            BACnetPointFactory(device=self.online_device)
        for _ in range(2):
            BACnetPointFactory(device=self.offline_device)

    def test_dashboard_integration_complete_flow(self):
        response = self.client.get(reverse("discovery:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BACnet Device Discovery")
        self.assertEqual(response.context["total_devices"], 3)
        self.assertEqual(response.context["offline_devices"], 1)
        self.assertEqual(response.context["total_points"], 6)

    def test_dashboard_with_empty_database(self):
        BACnetDevice.objects.all().delete()

        url = reverse("discovery:dashboard")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BACnet Device Discovery")
        self.assertEqual(response.context["total_devices"], 0)
        self.assertEqual(response.context["offline_devices"], 0)
        self.assertEqual(response.context["total_points"], 0)

    def test_dashboard_database_queries(self):
        device1 = BACnetDeviceFactory()
        device2 = BACnetDeviceFactory()

        for _ in range(5):
            BACnetPointFactory(device=device1)
        for _ in range(2):
            BACnetPointFactory(device=device2)

        response = self.client.get(reverse("discovery:dashboard"))

        devices = response.context["devices"]
        device1_data = devices.get(id=device1.id)
        device2_data = devices.get(id=device2.id)

        self.assertEqual(device1_data.point_count, 5)
        self.assertEqual(device2_data.point_count, 2)

    def test_dashboard_ordering(self):
        from datetime import timedelta

        from django.utils import timezone

        old_device = BACnetDeviceFactory(last_seen=timezone.now() - timedelta(hours=2))
        new_device = BACnetDeviceFactory(
            last_seen=timezone.now() - timedelta(minutes=30)
        )

        response = self.client.get(reverse("discovery:dashboard"))
        devices = list(response.context["devices"])

        self.assertEqual(devices[0].id, new_device.id)
        self.assertEqual(devices[1].id, old_device.id)


class TestDeviceDetailIntegration(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.device = BACnetDeviceFactory(points_read=True)

        self.analog_input = BACnetPointFactory(
            device=self.device,
            object_type="analogInput",
            instance_number=1,
            object_name="Temperature Sensor",
        )
        self.binary_input = BACnetPointFactory(
            device=self.device,
            object_type="binaryInput",
            instance_number=2,
            object_name="Door Status",
        )
        self.analog_output = BACnetPointFactory(
            device=self.device, object_type="analogOutput", instance_number=3
        )

    @patch("discovery.views.BACnetService")
    def test_device_detail_integration_complete_flow(self, mock_ensure_client):
        mock_service = Mock()
        mock_ensure_client.return_value = mock_service
        response = self.client.get(
            reverse("discovery:device_detail", args=[self.device.device_id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Device {self.device.device_id}")
        self.assertEqual(response.context["device"], self.device)
        self.assertEqual(response.context["point_count"], 3)
        self.assertTrue(response.context["points_loaded_recently"])
        points_by_type = response.context["points_by_type"]
        self.assertIn("analogInput", points_by_type)
        self.assertIn("binaryInput", points_by_type)

    def test_device_detail_404_for_nonexistent_device(self):
        response = self.client.get(reverse("discovery:device_detail", args=[99999]))

        self.assertEqual(response.status_code, 404)

    @patch("discovery.views._build_device_context")
    @patch("discovery.views._organise_points_by_type")
    def test_device_detail_helper_functions_called(
        self, mock_trigger, mock_organise, mock_context
    ):
        mock_organise.return_value = {"analogInput": [self.analog_input]}
        mock_context.return_value = {
            "device": self.device,
            "points": self.device.points.all(),
            "points_by_type": {"analogInput": [self.analog_input]},
            "point_count": 6,
            "points_loaded_recently": True,
        }

        url = reverse("discovery:device_detail", args=[self.device.device_id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        mock_trigger.assert_called_once()
        mock_organise.assert_called_once()
        mock_context.assert_called_once()

        from unittest.mock import ANY

        mock_trigger.assert_called_with(self.device, ANY)
        mock_organise.assert_called_with(ANY)
        mock_context.assert_called_with(self.device, ANY, mock_organise.return_value)

    def test_device_detail_helper_functions_integration(self):
        url = reverse("discovery:device_detail", args=[self.device.device_id])
        response = self.client.get(url)

        points_by_type = response.context["points_by_type"]
        self.assertIn("analogInput", points_by_type)
        self.assertIn("binaryInput", points_by_type)

        self.assertIn("device", response.context)
        self.assertIn("point_count", response.context)
        self.assertIn("points_loaded_recently", response.context)


class TestAPIEndpointIntegration(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.device = BACnetDeviceFactory()

        self.analog_point = BACnetPointFactory(
            device=self.device,
            object_type="analogInput",
            instance_number=1,
            present_value="25.5",
            units="°C",
        )
        self.binary_point = BACnetPointFactory(
            device=self.device,
            object_type="binaryInput",
            instance_number=2,
            present_value="1",
        )

    @patch("discovery.views.BACnetService")
    def test_start_discovery_integration(self, mock_ensure_client):
        mock_service = Mock()
        mock_ensure_client.return_value = mock_service

        url = reverse("discovery:start_discovery")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("Device discovery completed", data["message"])

        mock_service.discover_devices.assert_called_once()

    @patch("discovery.views.BACnetService")
    def test_discover_device_points_integration(self, mock_ensure_client):
        mock_service = Mock()
        mock_ensure_client.return_value = mock_service

        url = reverse("discovery:discover_device_points", args=[self.device.device_id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["device_id"], self.device.device_id)
        self.assertIn("Discovered", data["message"])

        mock_service.discover_device_points.assert_called_once()

    @patch("discovery.views.BACnetService")
    def test_read_point_values_integration(self, mock_ensure_client):
        mock_service = Mock()
        mock_ensure_client.return_value = mock_service

        url = reverse("discovery:read_point_values", args=[self.device.device_id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        mock_service.collect_all_readings.assert_called_once()

    @patch("discovery.views.BACnetService")
    def test_get_device_values_api_integration(self, mock_ensure_client):
        mock_service = Mock()
        mock_ensure_client.return_value = mock_service

        url = reverse("discovery:get_device_value_api", args=[self.device.device_id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["device_id"], self.device.device_id)
        self.assertEqual(data["total_points"], 2)
        self.assertIsInstance(data["points"], list)

    def test_device_list_api_integration(self):
        url = reverse("discovery:device_list_api")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("count", data)
        self.assertIn("devices", data)
        self.assertEqual(data["count"], 2)

    def test_clear_devices_integration(self):
        url = reverse("discovery:clear_devices")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(BACnetDevice.objects.filter(is_active=True).count(), 0)
