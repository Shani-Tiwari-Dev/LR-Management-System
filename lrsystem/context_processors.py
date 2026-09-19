import hashlib

from django.conf import settings


def _hash_of(path):
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()[:10]
    except OSError:
        return "0"


# Read once per process. The value only changes when the stylesheet does, which
# is what lets the browser cache it for a year and still pick up edits.
_ASSET_VERSION = _hash_of(settings.BASE_DIR / "static" / "css" / "app.css")


def asset_version(request):
    return {"asset_version": _ASSET_VERSION}
