import logging
from functools import wraps

from django.shortcuts import get_object_or_404

from .exceptions import BACnetError, ConfigurationError
from .models import BACnetDevice

logger = logging.getLogger(__name__)


def create_error_response_func():
    from .views import create_error_response

    return create_error_response


def requires_device_and_client(view_func):
    @wraps(view_func)
    def wrapper(request, device_id, *args, **kwargs):
        try:
            from .views import ensure_bacnet_client

            create_error_response = create_error_response_func()

            device = get_object_or_404(BACnetDevice, device_id=device_id)
            client = ensure_bacnet_client()

            return view_func(request, device_id, device, client, *args, **kwargs)

        except ConfigurationError as e:
            logger.exception(
                f"Configuration error in {view_func.__name__}"
                f" for device {device_id}: {e}"
            )
            return create_error_response(e)
        except BACnetError as e:
            logger.exception(
                f"BACnet error in {view_func.__name__} for device {device_id}: {e}"
            )
            return create_error_response(e)
        except Exception as e:
            logger.exception(
                f"Unexpected error in {view_func.__name__} for device {device_id}: {e}"
            )
            return create_error_response(e)

    return wrapper


def requires_client_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            from .views import ensure_bacnet_client

            create_error_response = create_error_response_func()

            client = ensure_bacnet_client()
            return view_func(request, client, *args, **kwargs)

        except ConfigurationError as e:
            logger.exception(f"Configuration error in {view_func.__name__}: {e}")
            return create_error_response(e)
        except BACnetError as e:
            logger.exception(f"BACnet error in {view_func.__name__}: {e}")
            return create_error_response(e)
        except Exception as e:
            logger.exception(f"Unexpected error in {view_func.__name__}: {e}")
            return create_error_response(e)

    return wrapper
