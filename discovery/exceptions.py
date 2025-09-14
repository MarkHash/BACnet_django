class BACnetError(Exception):
    """Base exception for all BACnet-related errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DeviceError(BACnetError):
    """Base for device-related errors."""

    pass


class PointError(BACnetError):
    """Base for point-related errors."""

    pass


class ConfigurationError(BACnetError):
    """Base for config-related errors."""

    pass


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
