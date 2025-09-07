from unittest.mock import Mock, patch

import pytest

from discovery.bacnet_client import DjangoBACnetClient
from discovery.exceptions import DeviceNotFoundByAddressError
from discovery.models import BACnetDevice

from .test_base import BACnetPointFactory, BaseTestCase

patcher = patch(
    "discovery.bacnet_client.BIPSimpleApplication.__init__", return_value=None
)
patcher.start()


class TestGetDeviceByAddress(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = DjangoBACnetClient(None, None, None)

    @patch("discovery.bacnet_client.BACnetDevice.objects.get")
    def test_get_device_by_address_success(self, mock_get):
        mock_device = Mock(device_id=123, address="192.168.1.100")
        mock_get.return_value = mock_device

        result = self.client._get_device_by_address("192.168.1.100")

        assert result == mock_device
        mock_get.assert_called_once_with(address="192.168.1.100")

    @patch("discovery.bacnet_client.BACnetDevice.objects.get")
    def test_get_device_by_address_not_found(self, mock_get):
        mock_get.side_effect = BACnetDevice.DoesNotExist()

        with pytest.raises(DeviceNotFoundByAddressError) as exc_info:
            self.client._get_device_by_address("192.168.1.100")

        assert "192.168.1.100" in str(exc_info.value)
        mock_get.assert_called_once_with(address="192.168.1.100")


class TestDispatchResponseHandler(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = DjangoBACnetClient(None, None, None)
        self.mock_device = Mock(device_id=123)

    @patch.object(DjangoBACnetClient, "_handle_object_list_response")
    def test_dispatch_object_list_response(self, mock_handle):
        mock_apdu = Mock()
        mock_apdu.objectIdentifier = ["device", 123]
        mock_apdu.propertyIdentifier = "objectList"

        self.client._dispatch_response_handler(mock_apdu, self.mock_device)
        mock_handle.assert_called_once_with(mock_apdu, self.mock_device)

    @patch.object(DjangoBACnetClient, "_handle_present_value_response")
    def test_dispatch_present_value_response(self, mock_handle):
        mock_apdu = Mock()
        mock_apdu.objectIdentifier = ["analogInput", 1]
        mock_apdu.propertyIdentifier = "presentValue"

        self.client._dispatch_response_handler(mock_apdu, self.mock_device)
        mock_handle.assert_called_once_with(mock_apdu, self.mock_device)

    @patch.object(DjangoBACnetClient, "_handle_object_name_response")
    def test_dispatch_object_name_response(self, mock_handle):
        mock_apdu = Mock()
        mock_apdu.objectIdentifier = ["analogInput", 1]
        mock_apdu.propertyIdentifier = "objectName"

        self.client._dispatch_response_handler(mock_apdu, self.mock_device)
        mock_handle.assert_called_once_with(mock_apdu, self.mock_device)

    @patch.object(DjangoBACnetClient, "_handle_units_response")
    def test_dispatch_units_response(self, mock_handle):
        mock_apdu = Mock()
        mock_apdu.objectIdentifier = ["analogInput", 1]
        mock_apdu.propertyIdentifier = "units"

        self.client._dispatch_response_handler(mock_apdu, self.mock_device)
        mock_handle.assert_called_once_with(mock_apdu, self.mock_device)


class TestHandleObjectListResponse(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = DjangoBACnetClient(None, None, None)
        self.mock_device = Mock(device_id=123)

    @patch.object(DjangoBACnetClient, "_parse_object_list")
    @patch.object(DjangoBACnetClient, "_save_points_to_database")
    def test_handle_object_list_with_points(self, mock_save, mock_parse):
        mock_apdu = Mock()
        mock_apdu.propertyValue = "mock_property_value"
        mock_points = [
            {"type": "analogInput", "instance": 1, "identifier": "analogInput:1"},
            {"type": "analogOutput", "instance": 2, "identifier": "analogOutput:2"},
        ]

        mock_parse.return_value = mock_points

        self.client.callback = Mock()
        self.client._handle_object_list_response(mock_apdu, self.mock_device)
        mock_parse.assert_called_once_with("mock_property_value", 123)
        mock_save.assert_called_once_with(self.mock_device, mock_points)

        self.client.callback.assert_called_once_with(
            "points_found", {"device_id": 123, "point_count": 2}
        )

    @patch.object(DjangoBACnetClient, "_parse_object_list")
    @patch.object(DjangoBACnetClient, "_save_points_to_database")
    def test_handle_object_list_no_points(self, mock_save, mock_parse):
        mock_apdu = Mock()
        mock_apdu.propertyValue = "mock_property_value"

        mock_parse.return_value = []

        self.client.callback = Mock()
        self.client._handle_object_list_response(mock_apdu, self.mock_device)
        mock_parse.assert_called_once_with("mock_property_value", 123)
        mock_save.assert_not_called()
        self.client.callback.assert_not_called()

    @patch.object(DjangoBACnetClient, "_parse_object_list")
    @patch.object(DjangoBACnetClient, "_save_points_to_database")
    def test_handle_object_list_no_callback(self, mock_save, mock_parse):
        mock_apdu = Mock()
        mock_points = [
            {"type": "analogInput", "instance": 1, "identifier": "analogInput:1"}
        ]
        mock_parse.return_value = mock_points
        self.client.callback = None

        self.client._handle_object_list_response(mock_apdu, self.mock_device)
        mock_save.assert_called_once_with(self.mock_device, mock_points)


class TestConvertUnitsEnumToText(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = DjangoBACnetClient(None, None, None)

    @patch("discovery.bacnet_client.EngineeringUnits")
    def test_convert_known_unit(self, mock_engineering_units):
        mock_unit = Mock()
        mock_unit.__str__ = Mock(return_value="EngineeringUnit(degreesCelsius)")
        mock_engineering_units.return_value = mock_unit

        result = self.client._convert_units_enum_to_text(64)

        assert result == "°C"
        mock_engineering_units.assert_called_once_with(64)

    @patch("discovery.bacnet_client.EngineeringUnits")
    def test_convert_unknown_unit(self, mock_engineering_units):
        mock_unit = Mock()
        mock_unit.__str__ = Mock(return_value="EngineeringUnit(someUnknownUnit)")
        mock_engineering_units.return_value = mock_unit

        result = self.client._convert_units_enum_to_text(999)

        assert result == "someUnknownUnit"
        mock_engineering_units.assert_called_once_with(999)

    def test_convert_invalid_units_code(self):
        result = self.client._convert_units_enum_to_text(-1)
        assert result == "unknown-units--1"

    @patch("discovery.bacnet_client.EngineeringUnits")
    def test_convert_percent_unit(self, mock_engineering_units):
        mock_unit = Mock()
        mock_unit.__str__ = Mock(return_value="EngineeringUnit(percent)")
        mock_engineering_units.return_value = mock_unit

        result = self.client._convert_units_enum_to_text(98)

        assert result == "%"


class TestReadPointValue(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = DjangoBACnetClient(None, None, None)

    @patch("discovery.bacnet_client.BACnetDevice.objects.get")
    @patch("discovery.bacnet_client.Address")
    @patch("discovery.bacnet_client.ReadPropertyRequest")
    @patch("discovery.bacnet_client.IOCB")
    def test_read_point_value_success(
        self, mock_iocb, mock_request, mock_address, mock_get
    ):
        mock_device = Mock(device_id=123, address="192.168.1.100")
        mock_get.return_value = mock_device

        mock_address_instance = Mock()
        mock_address.return_value = mock_address_instance

        mock_request_instance = Mock()
        mock_request.return_value = mock_request_instance

        mock_iocb_instance = Mock()
        mock_iocb.return_value = mock_iocb_instance

        self.client.request_io = Mock()

        self.client.read_point_value(123, "analogInput", 1, "presentValue")

        mock_get.assert_called_once_with(device_id=123)

        mock_request.assert_called_once_with(
            objectIdentifier=("analogInput", 1), propertyIdentifier="presentValue"
        )

        self.client.request_io.assert_called_once_with(mock_iocb_instance)

    @patch("discovery.bacnet_client.BACnetDevice.objects.get")
    def test_read_point_value_device_not_found(self, mock_get):
        from discovery.exceptions import DeviceNotFoundError

        mock_get.side_effect = BACnetDevice.DoesNotExist()

        with pytest.raises(DeviceNotFoundError) as exc_info:
            self.client.read_point_value(999, "analogInput", 1)

        assert "999" in str(exc_info.value)


class TestReadAllPointValues(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = DjangoBACnetClient(None, None, None)

        self.analog_point = BACnetPointFactory(
            device=self.device, object_type="analogInput", instance_number=1
        )
        self.binary_point = BACnetPointFactory(
            device=self.device, object_type="binaryInput", instance_number=2
        )

    @patch.object(DjangoBACnetClient, "read_point_value")
    @patch("discovery.bacnet_client.BACnetDevice.objects.get")
    def test_read_all_point_values_success(self, mock_get, mock_read_point):
        mock_get.return_value = self.device

        self.client.callback = Mock()
        self.client.read_all_point_values(self.device.device_id)

        # expected_calls = {
        #     ((self.device.device_id, "analogInput", 1, "presentValue"),),
        #     ((self.device.device_id, "binaryInput", 2, "presentValue"),),
        # }

        assert mock_read_point.call_count >= 2

        self.client.callback.assert_called_once()
