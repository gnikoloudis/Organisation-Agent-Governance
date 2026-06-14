import os
import httpx2
from services.api_client import API_BASE_URL, handle_response

STREAMLIT_MODE = os.environ.get("STREAMLIT_MODE", "direct")

def export_assets(selected_items, base_path):
    if STREAMLIT_MODE == "api":
        selected_ids = [item["id"] for item in selected_items]
        payload = {
            "selected_ids": selected_ids,
            "base_path": base_path
        }
        response = httpx2.post(f"{API_BASE_URL}/api/exporter/run", json=payload)
        data = handle_response(response)
        return data["exported_files"]
    else:
        from core.exporter import export_assets as core_export
        return core_export(selected_items, base_path)
