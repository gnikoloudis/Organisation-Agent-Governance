import os
import sys

# Add workspace directory to sys.path so we can import core and database
sys.path.append("d:/Python_Projects/Agent_Helper")

from core.skills import create_skill, get_skills, get_skill_by_id, update_skill, delete_skill
from core.rules import create_rule, get_rules, get_rule_by_id, update_rule, delete_rule
from core.workflows import create_workflow, get_workflows, get_workflow_by_id, update_workflow, delete_workflow
from core.mcp import create_mcp, get_mcps, get_mcp_by_id, update_mcp, delete_mcp
from core.exceptions import AssetValidationError, AssetNotFoundError, AssetFetchError
from database.db_manager import init_db

def test_skills():
    print("Testing Skills core functions...")
    
    # 1. Create a skill
    skill_content = "---\ntitle: Test Skill\ncategory: test, skill\ndescription: Test description\n---\n# Test Body"
    new_id = create_skill(
        name="Temporary Skill",
        storage_type="Markdown Text",
        content=skill_content,
        file_blob=None,
        file_name=None,
        description="Temp",
        tags="temp",
        reference_url="https://google.com"
    )
    assert new_id is not None
    print(f"  Skill created with ID: {new_id}")
    
    # 2. Retrieve skill and verify frontmatter override
    item = get_skill_by_id(new_id)
    assert item["name"] == "Test Skill"
    assert "test, skill" in item["tags"]
    assert "Test description" in item["description"]
    assert "google.com" in item["description"]
    print("  Frontmatter override and reference parsing verified.")
    
    # 3. Update skill file payload
    file_bytes = b"print('Hello world')"
    file_name = "test_script.py"
    update_skill(
        item_id=new_id,
        name="Updated Skill",
        content="# Simple script",
        description="New desc",
        tags="testing",
        reference_url=None,
        file_blob=file_bytes,
        file_name=file_name
    )
    
    updated_item = get_skill_by_id(new_id)
    assert updated_item["name"] == "Updated Skill"
    assert updated_item["file_blob"] == file_bytes
    assert updated_item["file_name"] == file_name
    print("  Skill update and file blob persistence verified.")
    
    # 4. Delete skill
    delete_skill(new_id)
    try:
        get_skill_by_id(new_id)
        assert False, "Should have raised AssetNotFoundError"
    except AssetNotFoundError:
        print("  Skill deletion verified.")
        
def test_mcp_validation():
    print("Testing MCP schema validation...")
    
    # 1. Valid MCP JSON
    valid_config = '{"mcpServers": {"test-server": {"command": "node", "args": ["index.js"]}}}'
    mcp_id = create_mcp(
        name="Test MCP",
        storage_type="JSON Config",
        content=valid_config,
        file_blob=None,
        file_name=None,
        description="Test MCP",
        tags="test"
    )
    assert mcp_id is not None
    print(f"  Valid MCP created with ID: {mcp_id}")
    
    # 2. Invalid MCP JSON (Syntax Error)
    try:
        invalid_json = '{"mcpServers": {invalid}'
        create_mcp("Invalid JSON MCP", "JSON Config", invalid_json, None, None, "test", "test")
        assert False, "Should have raised JSON syntax error"
    except AssetValidationError as e:
        assert "Syntax Error" in str(e) or "JSON" in str(e)
        print("  Invalid JSON Syntax rejection verified.")
        
    # 3. Invalid MCP Config (Schema Violation - command missing)
    try:
        invalid_schema = '{"mcpServers": {"test-server": {"args": []}}}'
        create_mcp("Invalid Schema MCP", "JSON Config", invalid_schema, None, None, "test", "test")
        assert False, "Should have raised Schema error"
    except AssetValidationError as e:
        assert "Schema Error" in str(e)
        print("  Invalid MCP Schema rejection verified.")
        
    # Clean up valid one
    delete_mcp(mcp_id)
    print("  MCP clean up completed.")

if __name__ == "__main__":
    init_db()
    test_skills()
    test_mcp_validation()
    print("ALL CORE UNIT TESTS PASSED!")

