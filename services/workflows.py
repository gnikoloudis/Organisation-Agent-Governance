import os
import httpx2
from services.api_client import API_BASE_URL, handle_response

STREAMLIT_MODE = os.environ.get("STREAMLIT_MODE", "direct")

def get_workflows():
    if STREAMLIT_MODE == "api":
        response = httpx2.get(f"{API_BASE_URL}/api/workflows")
        return handle_response(response)
    else:
        from core.workflows import get_workflows as core_get
        return core_get()

def get_workflow_by_id(item_id):
    if STREAMLIT_MODE == "api":
        response = httpx2.get(f"{API_BASE_URL}/api/workflows/{item_id}")
        return handle_response(response)
    else:
        from core.workflows import get_workflow_by_id as core_get_by_id
        return core_get_by_id(item_id)

def create_workflow(name, content, description, tags):
    if STREAMLIT_MODE == "api":
        payload = {
            "name": name,
            "content": content,
            "description": description,
            "tags": tags
        }
        response = httpx2.post(f"{API_BASE_URL}/api/workflows", json=payload)
        data = handle_response(response)
        return data["id"]
    else:
        from core.workflows import create_workflow as core_create
        return core_create(name, content, description, tags)

def update_workflow(item_id, name, content, description, tags):
    if STREAMLIT_MODE == "api":
        payload = {
            "name": name,
            "content": content,
            "description": description,
            "tags": tags
        }
        response = httpx2.put(f"{API_BASE_URL}/api/workflows/{item_id}", json=payload)
        data = handle_response(response)
        return data["id"]
    else:
        from core.workflows import update_workflow as core_update
        return core_update(item_id, name, content, description, tags)

def delete_workflow(item_id):
    if STREAMLIT_MODE == "api":
        response = httpx2.delete(f"{API_BASE_URL}/api/workflows/{item_id}")
        handle_response(response)
    else:
        from core.workflows import delete_workflow as core_delete
        core_delete(item_id)
