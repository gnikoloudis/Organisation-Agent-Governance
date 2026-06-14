import os
import sys
import base64
import shutil
import pytest
from fastapi.testclient import TestClient

# Resolve workspace path and append to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 1. Isolate Database path BEFORE importing app
import database.db_manager
TEST_DB_PATH = "test_agent_customizations.db"
database.db_manager.DB_PATH = TEST_DB_PATH

from database.db_manager import init_db
from main_api import app

# Initialize test database
init_db()
client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    # Clean the customizations table before each test
    conn = database.db_manager.get_connection()
    conn.execute("DELETE FROM customizations")
    conn.commit()
    conn.close()
    yield

def teardown_module():
    # Clean up test database file and test export folder
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass
            
    test_export_path = ".agent_test"
    if os.path.exists(test_export_path):
        try:
            shutil.rmtree(test_export_path)
        except Exception:
            pass


# =====================================================================
# CATEGORY 1: SKILLS
# =====================================================================

def test_skills_create_and_get():
    """Test 1: Creating and retrieving a standard skill asset."""
    payload = {
        "name": "Test Markdown Skill",
        "storage_type": "Markdown Text",
        "content": "# Markdown Instructions",
        "description": "Test description",
        "tags": "skills, test",
        "reference_url": "https://example.com/ref"
    }
    
    # POST
    response = client.post("/api/skills", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Markdown Skill"
    assert data["type"] == "Markdown Text"
    assert "ref" in data["description"]
    
    # GET by ID
    item_id = data["id"]
    get_response = client.get(f"/api/skills/{item_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Test Markdown Skill"


def test_skills_file_upload_and_download():
    """Test 2: Creating a file-upload skill using base64 and downloading it."""
    file_content = b"def test_func():\n    return 'Testing'"
    file_b64 = base64.b64encode(file_content).decode("utf-8")
    
    payload = {
        "name": "Test File Skill",
        "storage_type": "Real File Upload",
        "content": "Python Script File",
        "file_content_base64": file_b64,
        "file_name": "test_script.py",
        "description": "Uploaded python file",
        "tags": "upload"
    }
    
    # POST
    response = client.post("/api/skills", json=payload)
    assert response.status_code == 201
    data = response.json()
    item_id = data["id"]
    
    # GET Download
    download_response = client.get(f"/api/skills/{item_id}/download")
    assert download_response.status_code == 200
    assert download_response.content == file_content
    assert "filename=test_script.py" in download_response.headers["Content-Disposition"]


# =====================================================================
# CATEGORY 2: RULES
# =====================================================================

def test_rules_create_and_list():
    """Test 1: Creating a rule and listing all rule assets."""
    payload = {
        "name": "System Constraints",
        "storage_type": "Markdown Text",
        "content": "# Constraints",
        "description": "Crucial guidelines",
        "tags": "rules, production"
    }
    
    # POST
    response = client.post("/api/rules", json=payload)
    assert response.status_code == 201
    
    # GET list
    list_response = client.get("/api/rules")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["name"] == "System Constraints"


def test_rules_update():
    """Test 2: Creating a rule and updating its contents and tags."""
    # Create
    payload = {
        "name": "Initial Rule",
        "storage_type": "Markdown Text",
        "content": "Initial Content",
        "description": "Desc",
        "tags": "init"
    }
    create_response = client.post("/api/rules", json=payload)
    item_id = create_response.json()["id"]
    
    # PUT update
    update_payload = {
        "name": "Updated Rule Name",
        "content": "Updated Content Here",
        "description": "Updated Description",
        "tags": "new-tag, updated",
        "reference_url": "https://google.com"
    }
    update_response = client.put(f"/api/rules/{item_id}", json=update_payload)
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Updated Rule Name"
    assert data["content"] == "Updated Content Here"
    assert "new-tag" in data["tags"]
    assert "google.com" in data["description"]


# =====================================================================
# CATEGORY 3: WORKFLOWS
# =====================================================================

def test_workflows_create():
    """Test 1: Creating a workflow bookmark."""
    payload = {
        "name": "Test Workflow Bookmark",
        "content": "https://workflows.example.com",
        "description": "Workflow documentation",
        "tags": "workflow, bookmark"
    }
    
    response = client.post("/api/workflows", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Workflow Bookmark"
    assert data["type"] == "Web Bookmark"
    assert data["content"] == "https://workflows.example.com"


def test_workflows_delete():
    """Test 2: Deleting a workflow bookmark and verifying removal."""
    payload = {
        "name": "Workflow to Delete",
        "content": "https://workflows.example.com/delete",
        "description": "Temp Workflow",
        "tags": "temp"
    }
    create_response = client.post("/api/workflows", json=payload)
    item_id = create_response.json()["id"]
    
    # DELETE
    delete_response = client.delete(f"/api/workflows/{item_id}")
    assert delete_response.status_code == 200
    
    # GET verify 404
    get_response = client.get(f"/api/workflows/{item_id}")
    assert get_response.status_code == 404


# =====================================================================
# CATEGORY 4: MCP SERVICES
# =====================================================================

def test_mcp_create_valid():
    """Test 1: Creating a valid JSON MCP service asset."""
    valid_mcp_content = '{"mcpServers": {"git-server": {"command": "git", "args": ["status"]}}}'
    payload = {
        "name": "Git MCP Service",
        "storage_type": "JSON Config",
        "content": valid_mcp_content,
        "description": "Git repository operations",
        "tags": "git, mcp"
    }
    
    response = client.post("/api/mcp", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Git MCP Service"
    assert data["content"] == valid_mcp_content


def test_mcp_create_invalid_schema():
    """Test 2: Verifying that invalid MCP JSON configuration is rejected."""
    # Missing required field "command" inside server config
    invalid_mcp_content = '{"mcpServers": {"git-server": {"args": ["status"]}}}'
    payload = {
        "name": "Invalid MCP Service",
        "storage_type": "JSON Config",
        "content": invalid_mcp_content,
        "description": "Should fail schema validation",
        "tags": "failed"
    }
    
    response = client.post("/api/mcp", json=payload)
    assert response.status_code == 422
    assert "Schema Error" in response.json()["detail"]


# =====================================================================
# CATEGORY 5: EXPORTER
# =====================================================================

def test_exporter_run_success():
    """Test 1: Successfully running the exporter for multiple assets."""
    # Create test skill
    skill_payload = {
        "name": "Export Skill",
        "storage_type": "Markdown Text",
        "content": "# Export content",
        "description": "Export test",
        "tags": "exp"
    }
    skill_resp = client.post("/api/skills", json=skill_payload)
    skill_id = skill_resp.json()["id"]
    
    # Create test rule
    rule_payload = {
        "name": "Export Rule",
        "storage_type": "Markdown Text",
        "content": "# Export rules content",
        "description": "Export test",
        "tags": "exp"
    }
    rule_resp = client.post("/api/rules", json=rule_payload)
    rule_id = rule_resp.json()["id"]
    
    # Run exporter
    export_payload = {
        "selected_ids": [skill_id, rule_id],
        "base_path": ".agent_test"
    }
    
    response = client.post("/api/exporter/run", json=export_payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["exported_files"]) == 2
    
    # Verify physical file existence
    skill_path = os.path.join(".agent_test", "skills", "export_skill", "export_skill.md")
    rule_path = os.path.join(".agent_test", "rules", "export_rule", "export_rule.md")
    assert os.path.exists(skill_path)
    assert os.path.exists(rule_path)


def test_exporter_not_found():
    """Test 2: Verifying exporter fails with 404 when given non-existent IDs."""
    export_payload = {
        "selected_ids": [99999],  # Non-existent ID
        "base_path": ".agent_test"
    }
    
    response = client.post("/api/exporter/run", json=export_payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_relations_and_hierarchical_export():
    """Test 3: Verify creation, querying, deletion block, and hierarchical exporting of relations."""
    # 1. Create a parent skill
    parent_payload = {
        "name": "Developer Skill",
        "storage_type": "Markdown Text",
        "content": "# Dev instructions",
        "description": "Main dev skill",
        "tags": "dev, skill"
    }
    resp_parent = client.post("/api/skills", json=parent_payload)
    assert resp_parent.status_code == 201
    parent_id = resp_parent.json()["id"]

    # 2. Create a child rule
    child_rule_payload = {
        "name": "Style Guide Rule",
        "storage_type": "Markdown Text",
        "content": "# Guidelines",
        "description": "Dev styles",
        "tags": "dev, guidelines"
    }
    resp_child_rule = client.post("/api/rules", json=child_rule_payload)
    assert resp_child_rule.status_code == 201
    child_rule_id = resp_child_rule.json()["id"]

    # 3. Create another child skill (representing code asset)
    child_code_payload = {
        "name": "Dev Helper Code",
        "storage_type": "Real File Upload",
        "content": "def helper():\n    pass",
        "file_name": "helper_original.py",
        "description": "Helper functions",
        "tags": "helper"
    }
    resp_child_code = client.post("/api/skills", json=child_code_payload)
    assert resp_child_code.status_code == 201
    child_code_id = resp_child_code.json()["id"]

    # 4. Link child rule to parent skill as 'reference'
    link_rule_payload = {
        "child_id": child_rule_id,
        "relation_type": "reference",
        "relation_alias": "style_guide.md"
    }
    resp_link_rule = client.post(f"/api/skills/{parent_id}/relations", json=link_rule_payload)
    assert resp_link_rule.status_code == 201

    # 5. Link child code to parent skill as 'asset' with alias 'helper.py'
    link_code_payload = {
        "child_id": child_code_id,
        "relation_type": "asset",
        "relation_alias": "helper.py"
    }
    resp_link_code = client.post(f"/api/skills/{parent_id}/relations", json=link_code_payload)
    assert resp_link_code.status_code == 201

    # 6. Retrieve relations and verify
    resp_get_rels = client.get(f"/api/skills/{parent_id}/relations")
    assert resp_get_rels.status_code == 200
    relations = resp_get_rels.json()
    assert len(relations) == 2
    
    aliases = [r["relation_alias"] for r in relations]
    assert "style_guide.md" in aliases
    assert "helper.py" in aliases

    # 7. Assert deletion of child is prevented
    resp_del_child = client.delete(f"/api/rules/{child_rule_id}")
    assert resp_del_child.status_code == 422
    assert "referenced in a relationship" in resp_del_child.json()["detail"]

    # 8. Export the parent skill
    export_payload = {
        "selected_ids": [parent_id],
        "base_path": ".agent_test"
    }
    resp_export = client.post("/api/exporter/run", json=export_payload)
    assert resp_export.status_code == 200
    exported_files = resp_export.json()["exported_files"]

    # Verify folder structure
    parent_path = os.path.join(".agent_test", "skills", "developer_skill", "developer_skill.md")
    rule_rel_path = os.path.join(".agent_test", "skills", "developer_skill", "references", "style_guide.md")
    code_rel_path = os.path.join(".agent_test", "skills", "developer_skill", "assets", "helper.py")

    assert os.path.exists(parent_path)
    assert os.path.exists(rule_rel_path)
    assert os.path.exists(code_rel_path)

    with open(code_rel_path, "r", encoding="utf-8") as f:
        code_content = f.read()
    assert "def helper():" in code_content

    # 9. Delete relationship link, then check that deletion of child is now allowed
    resp_remove_link = client.request("DELETE", f"/api/skills/{parent_id}/relations", json=link_rule_payload)
    assert resp_remove_link.status_code == 200

    resp_del_child_allowed = client.delete(f"/api/rules/{child_rule_id}")
    assert resp_del_child_allowed.status_code == 200
