import logging
import traceback
from datetime import datetime

from bacpypes.apdu import ReadPropertyRequest, WhoIsRequest
from bacpypes.app import BIPSimpleApplication
from bacpypes.constructeddata import ArrayOf
from bacpypes.debugging import ModuleLogger, bacpypes_debugging
from bacpypes.iocb import IOCB
from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.primitivedata import ObjectIdentifier, Real, Unsigned, Integer

from .models import BACnetDevice, BACnetPoint, BACnetReading

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
_debug = 0
_log = ModuleLogger(globals())
# discovered_devices = {}
# device_points = {}


@bacpypes_debugging
class DjangoBACnetClient(BIPSimpleApplication):
    def __init__(self, callback, *args):
        if _debug:
            DjangoBACnetClient._debug("__init__%r", args)
        BIPSimpleApplication.__init__(self, *args)
        self.callback = callback

    def do_IAmRequest(self, apdu):
        if _debug:
            DjangoBACnetClient._debug("do_IAmRequest %r", apdu)

        try:
            logger.debug(f"Device discovered: {apdu.iAmDeviceIdentifier}")

            device_identifier = apdu.iAmDeviceIdentifier
            vendor_id = apdu.vendorID
            device_id = device_identifier[1]

            device, created = BACnetDevice.objects.get_or_create(
                device_id=device_id,
                defaults={
                    "address": str(apdu.pduSource),
                    "vendor_id": vendor_id,
                    "is_online": True,
                    "points_read": False,
                },
            )

            if not created:
                device.address = str(apdu.pduSource)
                device.vendor_id = vendor_id
                device.mark_seen()

            logger.debug(f"✓ Device {device_id} saved to database: {device.address}")

            if self.callback:
                self.callback(
                    "device_found",
                    {
                        "device_id": device_id,
                        "address": str(apdu.pduSource),
                        "vendor_id": vendor_id,
                        "created": created,
                    },
                )

        except Exception as e:
            logger.error(f"Error in do_IAMRequest: {e}")
            traceback.print_exc()

    def process_read_response(self, iocb):
        if _debug:
            DjangoBACnetClient._debug("process_read_response %r", iocb)

        try:
            if iocb.ioResponse:
                apdu = iocb.ioResponse
                device_address = str(apdu.pduSource)

                try:
                    device = BACnetDevice.objects.get(address=device_address)
                except BACnetDevice.DoesNotExist:
                    logger.error(
                        f"ReadProperty response from unknown device: {device_address}"
                    )
                    return
                print(f"+++{apdu.objectIdentifier[0]}, {apdu.propertyIdentifier}, {apdu.propertyValue}, {device.device_id}")

                if (
                    apdu.objectIdentifier[0] == "device"
                    and apdu.propertyIdentifier == "objectList"
                ):
                    points = self._parse_object_list(
                        apdu.propertyValue, device.device_id
                    )
                    if points:
                        self._save_points_to_database(device, points)
                        logger.debug(
                            f"✓ Saved {len(points)} points for device{device.device_id}"
                        )

                        if self.callback:
                            self.callback(
                                "points_found",
                                {
                                    "device_id": device.device_id,
                                    "point_count": len(points),
                                },
                            )
                elif apdu.propertyIdentifier == 'presentValue':
                    self._handle_present_value_response(apdu, device)
                elif apdu.propertyIdentifier == 'objectName':
                    print(f"apdu.propertyIdentifier == 'objectName'")
                    self._handle_object_name_response(apdu, device)
                elif apdu.propertyIdentifier == 'units':
                    print(f"apdu.propertyIdentifier == 'units'")
                    self._handle_units_response(apdu, device)

            elif iocb.ioError:
                logger.error(f"ReadProperty error: {iocb.ioError}")
            else:
                logger.error("ReadProperty timeout")

        except Exception as e:
            logger.error(f"Error processing ReadProperty response: {e}")
            traceback.print_exc()

    def _handle_present_value_response(self, apdu, device):
        try:
            object_type = apdu.objectIdentifier[0]
            instance_number = apdu.objectIdentifier[1]

            point = BACnetPoint.objects.get(
                device=device,
                object_type=object_type,
                instance_number=instance_number
            )

            if apdu.propertyValue.__class__.__name__ == 'Any':
                present_value = apdu.propertyValue.cast_out(Real)
            else:
                present_value = apdu.propertyValue.cast_out(Unsinged)
            print(f"Present_value: {present_value}, object_type: {object_type}")

            point.update_value(present_value)
            BACnetReading.objects.create(
                point=point,
                value=str(present_value)
            )

            logger.debug(f"✓ Updated {point.identifier} - {present_value}")

            if self.callback:
                self.callback('value_read', {
                    'point_id': point.id,
                    'identifier': point.identifier,
                    'value': present_value
                })
        except BACnetPoint.DoesNotExist:
            logger.debug(f"Point not found for value response: {object_type}: {instance_number}")
        except Exception as e:
            logger.debug(f"Error handling present value: {e}")
    
    def _handle_object_name_response(self, apdu, device):
        try:
            object_type = apdu.objectIdentifier[0]
            instance_number = apdu.objectIdentifier[1]

            point = BACnetPoint.objects.get(
                device=device,
                object_type=object_type,
                instance_number=instance_number
            )

            print(f"object_name: {apdu.propertyValue}")

            object_name = str(apdu.propertyValue)
            point.object_name = object_name
            point.save()

            logger.debug(f"✓ Updated name for {point.identifier}: {object_name}")

        except Exception as e:
            logger.debug(f"Error handling object name: {e}")

    def _handle_units_response(self, apdu, device):
        try:
            object_type = apdu.objectIdentifier[0]
            instance_number = apdu.objectIdentifier[1]

            point = BACnetPoint.objects.get(
                device=device,
                object_type=object_type,
                instance_number=instance_number
            )

            units = str(apdu.propertyValue)
            point.units = units
            point.save()
            logger.debug(f"✓ Updated units for {point.identifier}: {units}")

        except Exception as e:
            logger.debug(f"Error handling units: {e}")

    def read_point_value(self, device_id, object_type, instance_number, property_name='presentValue'):
        try:
            device = BACnetDevice.objects.get(device_id=device_id)
            device_address = Address(device.address)

            request = ReadPropertyRequest(
                objectIdentifier=(object_type, instance_number),
                propertyIdentifier=property_name
            )
            request.pduDestination = device_address

            iocb = IOCB(request)
            self.request_io(iocb)
            iocb.add_callback(self.process_read_response)

            logger.debug(f"✓ Reading {property_name} from {object_type}:{instance_number} on device {device_id}")
        except BACnetDevice.DoesNotExist:
            logger.debug(f"Device {device_id} not found")
        except Exception as e:
            logger.debug(f"Error reading point value: {e}")

    def read_all_point_values(self, device_id):
        try:
            device = BACnetDevice.objects.get(device_id=device_id)
            readable_points = device.points.filter(object_type__in=[
            'analogInput',
            'analogOutput',
            'analogValue',
            'binaryInput',
            'binaryOutput',
            'binaryValue',
            'multiStateInput',
            'multiStateOutput',
            'multiStateValue',
            ])
            logger.debug(f"✓ Reading values from {readable_points.count()} points on device {device_id}")
            
            for point in readable_points:
                self.read_point_value(device_id, point.object_type, point.instance_number, 'presentValue')

                if not point.object_name:
                    self.read_point_value(device_id, point.object_type, point.instance_number, 'objectName')
                if not point.units and point.object_type.startswith('analog'):
                    self.read_point_value(device_id, point.object_type, point.instance_number, 'units')
            
            if self.callback:
                self.callback('reading_values', {
                    'device_id': device_id,
                    'point_count': readable_points.count()
                })

        except BACnetDevice.DoesNotExist:
            logger.debug(f"Device {device_id} not found")
        except Exception as e:
            logger.debug(f"Error reading point value: {e}")


    def _parse_object_list(self, property_value, device_id):
        points = []

        try:
            if property_value.__class__.__name__ == "Any":
                object_list = property_value.cast_out(ArrayOf(ObjectIdentifier))
            else:
                object_list = property_value

            logger.debug(f"Device {device_id}: Object list length: {len(object_list)}")

            for i, obj_item in enumerate(object_list):
                if obj_item is None:
                    continue

                try:
                    obj_type_name = str(obj_item[0])
                    obj_instance_num = int(obj_item[1])

                    points.append(
                        {
                            "type": obj_type_name,
                            "instance": obj_instance_num,
                            "identifier": f"{obj_type_name}:{obj_instance_num}",
                        }
                    )
                except Exception as e:
                    logger.error(f"    Error parsing object {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"    Error parsing object list: {e}")
            return []

        return points

    def _save_points_to_database(self, device, points):
        for point_data in points:
            logger.debug(f"point_data: {point_data}")
            point, created = BACnetPoint.objects.get_or_create(
                device=device,
                object_type=point_data["type"],
                instance_number=point_data["instance"],
                defaults={
                    "identifier": point_data["identifier"]
                    }
            )

            if created:
                logger.debug(f"  ✓ Created point: {point.identifier}")
            else:
                logger.debug(f"  ○ Point exists: {point.identifier}")

        device.points_read = True
        device.save()

    def send_whois(self):
        """Send a WhoIs erquest as a global broadast"""

        if _debug:
            DjangoBACnetClient._debug("Send WhoIs request")

        try:
            request = WhoIsRequest()
            request.pduDestination = GlobalBroadcast()

            self.request(request)
            timestamp = datetime.now().strftime("%H:%M:%S")
            logger.debug(f"✓ Sent WhoIs broadcast at {timestamp}")

            if self.callback:
                self.callback("whois_sent", timestamp)

        except Exception as e:
            logger.error(f"Error sending WhoIs: {e}")

    def read_device_objects(self, device_id):
        if _debug:
            DjangoBACnetClient._debug("read_device_objects %r", device_id)

        try:
            device = BACnetDevice.objects.get(device_id=device_id)
            device_address = Address(device.address)

            request = ReadPropertyRequest(
                objectIdentifier=("device", device_id), propertyIdentifier="objectList"
            )
            request.pduDestination = device_address

            iocb = IOCB(request)
            self.request_io(iocb)
            iocb.add_callback(self.process_read_response)
            logger.debug(f"✓ Reading object list from device {device_id}")

        except BACnetDevice.DoesNotExist:
            logger.error(f"Device {device_id} not found in database")
        except Exception as e:
            logger.error(f"Error reading device objects: {e}")
            traceback.print_exc()

    def get_discovered_devices(self):
        devices = {}
        for device in BACnetDevice.objects.all():
            devices[device.device_id] = {
                "device_id": device.device_id,
                "address": device.address,
                "vendor_id": device.vendor_id,
                "last_seen": device.last_seen,
                "points_read": device.points_read,
            }
        return devices

    def get_device_points(self, device_id):
        try:
            device = BACnetDevice.objects.get(device_id=device_id)
            points = []
            for point in device.points.all():
                points.append(
                    {
                        "type": point.object_type,
                        "instance": point.instance_number,
                        "identifier": point.identifier,
                    }
                )
            return points
        except BACnetDevice.DoesNotExist:
            return []


def start_bacnet_discovery(callback=None):
    logger.debug("🚀 Starting BACnet discovery...")
    return True


def get_device_count():
    return BACnetDevice.count()


def get_online_device_count():
    return BACnetDevice.objects.filter(is_online=True).count()


def get_total_points():
    return BACnetPoint.objects.count()


def clear_all_devices():
    device_count = BACnetDevice.objects.count()
    point_count = BACnetPoint.objects.count()
    BACnetDevice.objects.all().delete()

    return device_count, point_count
