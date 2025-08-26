import json
import logging
import os
import sys
import threading
import time

from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.core import enable_sleeping, run
from bacpypes.local.device import LocalDeviceObject
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from .bacnet_client import DjangoBACnetClient, clear_all_devices
from .models import BACnetDevice, BACnetPoint

# Create your views here.
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

bacnet_client = None
bacnet_config = None


def load_bacnet_config():
    global bacnet_config
    if bacnet_config is None:
        try:
            logger.debug("Loading BAcnet configuration from BACpypes.ini...")
            original_argv = sys.argv.copy()
            ini_path = "./discovery/BACpypes.ini"
            if not os.path.exists(ini_path):
                logger.debug(f"{ini_path} not found in current directory")
                return None
            sys.argv = ["django_bacnet", "--ini", ini_path]
            args = ConfigArgumentParser(
                description="Django BACnet Discovery"
            ).parse_args()
            bacnet_config = args.ini
            sys.argv = original_argv

            logger.debug(f"✅ Configuration loaded:")
            logger.debug(f"   Device Name: {bacnet_config}")

        except Exception as e:
            logger.debug(f"Error loading BACnet configuration: {e}")
            sys.argv = original_argv
            bacnet_config = None

    return bacnet_config


def dashboard(request):
    devices = (
        BACnetDevice.objects.all()
        .annotate(point_count=Count("points"))
        .order_by("-last_seen")
    )

    context = {
        "devices": devices,
        "total_devices": devices.count(),
        "online_devices": devices.filter(is_online=True).count(),
        "total_points": BACnetPoint.objects.count(),
    }
    return render(request, "discovery/dashboard.html", context)


def device_detail(request, device_id):
    device = get_object_or_404(BACnetDevice, device_id=device_id)
    points = device.points.all().order_by("object_type", "instance_number")

    points_by_type = {}
    for point in points:
        if point.object_type not in points_by_type:
            points_by_type[point.object_type] = []
        points_by_type[point.object_type].append(point)

    context = {
        "device": device,
        "points": points,
        "points_by_type": points_by_type,
        "point_count": points.count(),
    }
    return render(request, "discovery/device_detail.html", context)


def ensure_bacnet_client():
    global bacnet_client

    if bacnet_client is None:
        logger.debug("Creating BACnet client...")

        # args = ConfigArgumentParser(description=__doc__).parse_args()
        config = load_bacnet_config()
        if config is None:
            raise Exception("Could not load BACnet configuration from BACpypes.ini")

        device = LocalDeviceObject(
            objectName=config.objectname,
            objectIdentifier=int(config.objectidentifier),
            maxApduLengthAccepted=int(config.maxapdulengthaccepted),
            segmentationSupported=config.segmentationsupported,
            vendorIdentifier=int(config.vendoridentifier),
        )
        logger.debug(f"Workstation info: {device}")

        LOCAL_IP = config.address

        def callback(event_type, data):
            logger.debug(f"BACnet event: {event_type} = {data}")

        bacnet_client = DjangoBACnetClient(callback, device, LOCAL_IP)

        def run_bacnet():
            enable_sleeping()
            run()

        bacnet_thread = threading.Thread(target=run_bacnet)
        bacnet_thread.daemon = True
        bacnet_thread.start()

        logger.debug("BACnet client started!")
    return bacnet_client


@csrf_exempt
def start_discovery(request):
    if request.method == "POST":
        try:
            client = ensure_bacnet_client()
            client.send_whois()

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Device discovery started"
                    f" - devices will appear in a few seconds",
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Error starting discovery: {str(e)}"}
            )

    return JsonResponse({"success": False, "message": "Invalid request"})


@csrf_exempt
def read_device_points(request, device_id):
    if request.method == "POST":
        try:
            logger.debug(f"device_ID: {device_id}")
            device = get_object_or_404(BACnetDevice, device_id=device_id)
            client = ensure_bacnet_client()
            client.read_device_points(device.device_id)

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Started reading points for device {device.device_id}",
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Error reading points: {str(e)}"}
            )

    return JsonResponse({"success": False, "message": "Invalid request"})


@csrf_exempt
def clear_devices(request):
    if request.method == "POST":
        try:
            device_count, point_count = clear_all_devices()

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Cleared {device_count} devices and {point_count} points",
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Error clearing devices: {str(e)}"}
            )

    return JsonResponse({"success": False, "message": "Invalid request"})


def device_list_api(request):
    devices = BACnetDevice.objects.all().values(
        "device_id", "address", "vendor_id", "is_online", "last_seen", "points_read"
    )

    return JsonResponse({"devices": list(devices), "count": len(devices)})

def test_api(request):
    return JsonResponse({
        'message': 'API is working!',
        'method': request.method,
        'path': request.path
    })