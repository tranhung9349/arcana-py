"""Optional local GeoIP2 database; no outbound calls or trust in forwarded IPs."""
from datetime import datetime, timezone
from ipaddress import ip_address
import os

from .models import Location


def ip_location(address):
    reason = "GEOIP_DATABASE_NOT_CONFIGURED"
    try:
        address_obj = ip_address(address)
        if not address_obj.is_global:
            reason = "PRIVATE_OR_LOCAL_IP"
        elif os.environ.get("RANDOMYST_GEOIP_DATABASE"):
            import geoip2.database
            with geoip2.database.Reader(os.environ["RANDOMYST_GEOIP_DATABASE"]) as reader:
                result = reader.city(str(address_obj))
            if result.location.longitude is not None:
                return Location(longitude=result.location.longitude, latitude=result.location.latitude, source="IP",
                                acquired_at=datetime.now(timezone.utc), fallback_reason="DEVICE_LOCATION_UNAVAILABLE")
            reason = "IP_COORDINATES_UNAVAILABLE"
    except (ValueError, OSError, ImportError):
        reason = "IP_LOOKUP_UNAVAILABLE"
    except Exception:
        # GeoIP address-not-found or invalid database must not prevent a draw.
        reason = "IP_LOOKUP_FAILED"
    return Location(longitude=105, source="DEFAULT", fallback_reason=reason)
