import os
import base64
import httpx2
from services.api_client import API_BASE_URL, handle_response

STREAMLIT_MODE = os.environ.get("STREAMLIT_MODE", "direct")

def get_skills():
    if STREAMLIT_MODE == "api":
        response = httpx2.get(f"{API_BASE_URL}/api/skills")
        items = handle_response(response)
        for item in items:
            if item["type"] == "Real File Upload":
                dl_resp = httpx2.get(f"{API_BASE_URL}/api/skills/{item['id']}/download")
                if dl_resp.status_code == 200:
                    item["file_blob"] = dl_resp.content
        return items
    else:
        from core.skills import get_skills as core_get
        return core_get()

def get_skill_by_id(item_id):
    if STREAMLIT_MODE == "api":
        response = httpx2.get(f"{API_BASE_URL}/api/skills/{item_id}")
        item = handle_response(response)
        if item["type"] == "Real File Upload":
            dl_resp = httpx2.get(f"{API_BASE_URL}/api/skills/{item_id}/download")
            if dl_resp.status_code == 200:
                item["file_blob"] = dl_resp.content
        return item
    else:
        from core.skills import get_skill_by_id as core_get_by_id
        return core_get_by_id(item_id)

def create_skill(name, storage_type, content, file_blob, file_name, description, tags, reference_url=""):
    if STREAMLIT_MODE == "api":
        file_b64 = base64.b64encode(file_blob).decode("utf-8") if file_blob else None
        payload = {
            "name": name,
            "storage_type": storage_type,
            "content": content,
            "file_content_base64": file_b64,
            "file_name": file_name,
            "description": description,
            "tags": tags,
            "reference_url": reference_url
        }
        response = httpx2.post(f"{API_BASE_URL}/api/skills", json=payload)
        data = handle_response(response)
        return data["id"]
    else:
        from core.skills import create_skill as core_create
        return core_create(name, storage_type, content, file_blob, file_name, description, tags, reference_url)

def update_skill(item_id, name, content, description, tags, reference_url="", file_blob=None, file_name=None):
    if STREAMLIT_MODE == "api":
        file_b64 = base64.b64encode(file_blob).decode("utf-8") if file_blob else None
        payload = {
            "name": name,
            "content": content,
            "file_content_base64": file_b64,
            "file_name": file_name,
            "description": description,
            "tags": tags,
            "reference_url": reference_url
        }
        response = httpx2.put(f"{API_BASE_URL}/api/skills/{item_id}", json=payload)
        data = handle_response(response)
        return data["id"]
    else:
        from core.skills import update_skill as core_update
        return core_update(item_id, name, content, description, tags, reference_url, file_blob, file_name)

def delete_skill(item_id):
    if STREAMLIT_MODE == "api":
        response = httpx2.delete(f"{API_BASE_URL}/api/skills/{item_id}")
        handle_response(response)
    else:
        from core.skills import delete_skill as core_delete
        core_delete(item_id)
