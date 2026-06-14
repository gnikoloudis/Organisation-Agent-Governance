import os
import httpx2
from core.exceptions import AssetValidationError, AssetNotFoundError, AssetFetchError

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8080").rstrip("/")

def handle_response(response):
    """Translates HTTP error codes into custom core exceptions or returns JSON."""
    if response.status_code in (200, 201):
        try:
            return response.json()
        except Exception:
            return response.content

    # Extract detail message
    try:
        detail = response.json().get("detail", "Unknown API error occurred.")
    except Exception:
        detail = f"HTTP Error {response.status_code}: {response.text}"

    if response.status_code == 422:
        raise AssetValidationError(detail)
    elif response.status_code == 404:
        raise AssetNotFoundError(detail)
    elif response.status_code == 400:
        raise AssetFetchError(detail)
    else:
        raise Exception(detail)
