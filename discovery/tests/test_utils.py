from discovery.views import (
    _build_device_context,
    _organise_points_by_type,
)

from .test_base import BACnetDeviceFactory, BACnetPointFactory, BaseTestCase


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
