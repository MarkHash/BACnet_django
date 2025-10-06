from django.http import JsonResponse
from django.utils import timezone


class BACnetError(Exception):
    """Base exception for all BACnet-related errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DeviceError(BACnetError):
    """Base for device-related errors."""


class PointError(BACnetError):
    """Base for point-related errors."""


class ConfigurationError(BACnetError):
    """Base for config-related errors."""


class DeviceNotFoundError(DeviceError):
    def __init__(self, device_id: int):
        self.device_id = device_id
        message = f"Device {device_id} not found"
        super().__init__(message, {"device_id": device_id})


class DeviceNotFoundByAddressError(DeviceError):
    def __init__(self, device_address: str):
        self.device_address = device_address
        message = f"No device found with address: {device_address}"
        super().__init__(message, {"device_address": device_address})


class PointNotFoundError(PointError):
    def __init__(
        self,
        message,
        device_id: int,
        object_types: str,
        instance_number: int,
        context: str = None,
    ):
        self.device_id = device_id
        self.object_types = object_types
        self.instance_number = instance_number
        self.context = context
        identifier = f"{object_types}:{instance_number}"
        message = f"Point {identifier} not found on device {device_id}"
        if context:
            message += f" ({context})"
        super().__init__(
            message,
            {
                "device_id": device_id,
                "object_types": object_types,
                "instance_number": instance_number,
                "identifier": identifier,
                "context": context,
            },
        )


class BACnetServiceError(Exception):
    pass


class BACnetConnectionError(BACnetServiceError):
    pass


class BACnetDeviceError(BACnetServiceError):
    def __init__(self, device_id, message, original_error=None):
        self.device_id = device_id
        self.original_error = original_error
        super().__init__(f"Device {device_id}: {message}")


class BACnetPropertyReadError(BACnetServiceError):
    def __init__(self, device_id, property_name, original_error=None):
        self.device_id = device_id
        self.property_name = property_name
        self.original_error = original_error
        super().__init__(f"Failed to read {property_name} from device {device_id}")


class BACnetBatchReadError(BACnetServiceError):
    def __init__(self, device_id, point_count, original_error=None):
        self.device_id = device_id
        self.point_count = point_count
        self.original_error = original_error
        super().__init__(
            f"Batch read failed for device {device_id} ({point_count} points)"
        )


class APIError(Exception):
    status_code = 500
    error_code = "INTERNAL_ERROR"
    message = "An internal error occurred"

    def to_response(self):
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "code": self.error_code,
                    "message": self.message,
                    "type": self.__class__.__name__,
                },
                "timestamp": timezone.now().isoformat(),
            },
            status=self.status_code,
        )


class ValidationError(APIError):
    status_code = 400
    error_code = "VALIDATION_ERROR"

    def __init__(self, message="Validation error"):
        self.message = message
        super().__init__()


class DeviceNotFoundAPIError(APIError):
    status_code = 404
    error_code = "DEVICE_NOT_FOUND"
    message = "Device not found"


class RateLimitExceededError(APIError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please try again later."
