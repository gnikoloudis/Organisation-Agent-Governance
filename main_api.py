import base64
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Database imports
from database.db_manager import get_customization_by_id, init_db

# Core exceptions
from core.exceptions import AssetValidationError, AssetFetchError, AssetNotFoundError

# Core services
from core.skills import get_skills, get_skill_by_id, create_skill, update_skill, delete_skill
from core.rules import get_rules, get_rule_by_id, create_rule, update_rule, delete_rule
from core.workflows import get_workflows, get_workflow_by_id, create_workflow, update_workflow, delete_workflow
from core.mcp import get_mcps, get_mcp_by_id, create_mcp, update_mcp, delete_mcp
from core.exporter import export_assets

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Agent Customization Hub REST API",
    description="REST API for managing Skills, Rules, Workflows, MCP Services, and Exports.",
    version="1.0.0",
    lifespan=lifespan
)

# Exception Handlers
@app.exception_handler(AssetValidationError)
def validation_error_handler(request: Request, exc: AssetValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": str(exc)}
    )

@app.exception_handler(AssetFetchError)
def fetch_error_handler(request: Request, exc: AssetFetchError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

@app.exception_handler(AssetNotFoundError)
def not_found_error_handler(request: Request, exc: AssetNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )

# Schemas
class AssetResponse(BaseModel):
    id: int
    category: str
    name: str
    type: str
    content: Optional[str] = None
    file_name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    created_at: str

    @classmethod
    def from_db(cls, row: dict):
        return cls(
            id=row["id"],
            category=row["category"],
            name=row["name"],
            type=row["type"],
            content=row["content"],
            file_name=row["file_name"],
            description=row["description"],
            tags=row["tags"],
            created_at=str(row["created_at"])
        )

class RelationCreate(BaseModel):
    child_id: int
    relation_type: str
    relation_alias: str

class RelationUpdate(BaseModel):
    child_id: int
    old_type: str
    old_alias: str
    new_type: str
    new_alias: str

class RelationResponse(BaseModel):
    parent_id: int
    child_id: int
    relation_type: str
    relation_alias: str
    child_asset: AssetResponse

    @classmethod
    def from_db_row(cls, row: dict):
        child_data = {
            "id": row["child_id"],
            "category": row["category"],
            "name": row["name"],
            "type": row["type"],
            "content": row["content"],
            "file_name": row["file_name"],
            "description": row["description"],
            "tags": row["tags"],
            "created_at": str(row["created_at"])
        }
        return cls(
            parent_id=row["parent_id"],
            child_id=row["child_id"],
            relation_type=row["relation_type"],
            relation_alias=row["relation_alias"],
            child_asset=AssetResponse(**child_data)
        )

class AssetCreate(BaseModel):
    name: str
    storage_type: str
    content: Optional[str] = None
    file_content_base64: Optional[str] = None
    file_name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    reference_url: Optional[str] = None

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    file_content_base64: Optional[str] = None
    file_name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    reference_url: Optional[str] = None

class WorkflowCreate(BaseModel):
    name: str
    content: str
    description: Optional[str] = None
    tags: Optional[str] = None

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None

class ExportRequest(BaseModel):
    selected_ids: List[int]
    base_path: str = ".agent"

# Helper function
def decode_base64_file(b64_str: str) -> bytes:
    try:
        return base64.b64decode(b64_str)
    except Exception:
        raise AssetValidationError("Invalid base64 encoding for file content.")


# ==========================================
# SKILLS ENDPOINTS
# ==========================================
@app.get("/api/skills", response_model=List[AssetResponse], tags=["Skills"])
def list_skills():
    return [AssetResponse.from_db(item) for item in get_skills()]

@app.get("/api/skills/{item_id}", response_model=AssetResponse, tags=["Skills"])
def read_skill(item_id: int):
    return AssetResponse.from_db(get_skill_by_id(item_id))

@app.post("/api/skills", response_model=AssetResponse, status_code=status.HTTP_201_CREATED, tags=["Skills"])
def add_skill(payload: AssetCreate):
    file_blob = decode_base64_file(payload.file_content_base64) if payload.file_content_base64 else None
    new_id = create_skill(
        name=payload.name,
        storage_type=payload.storage_type,
        content=payload.content,
        file_blob=file_blob,
        file_name=payload.file_name,
        description=payload.description,
        tags=payload.tags,
        reference_url=payload.reference_url or ""
    )
    return AssetResponse.from_db(get_skill_by_id(new_id))

@app.put("/api/skills/{item_id}", response_model=AssetResponse, tags=["Skills"])
def edit_skill(item_id: int, payload: AssetUpdate):
    file_blob = decode_base64_file(payload.file_content_base64) if payload.file_content_base64 else None
    update_skill(
        item_id=item_id,
        name=payload.name,
        content=payload.content,
        description=payload.description,
        tags=payload.tags,
        reference_url=payload.reference_url or "",
        file_blob=file_blob,
        file_name=payload.file_name
    )
    return AssetResponse.from_db(get_skill_by_id(item_id))

@app.delete("/api/skills/{item_id}", tags=["Skills"])
def remove_skill(item_id: int):
    delete_skill(item_id)
    return {"detail": f"Successfully deleted skill with ID {item_id}"}

@app.get("/api/skills/{item_id}/download", tags=["Skills"])
def download_skill_file(item_id: int):
    item = get_skill_by_id(item_id)
    if item["type"] != "Real File Upload" or not item["file_blob"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This asset does not contain an uploaded file blob.")
    return Response(
        content=item["file_blob"],
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={item['file_name']}"}
    )

@app.get("/api/skills/{item_id}/relations", response_model=List[RelationResponse], tags=["Skills"])
def get_skill_relations_api(item_id: int):
    from core.skills import get_skill_relations
    relations = get_skill_relations(item_id)
    return [RelationResponse.from_db_row(r) for r in relations]

@app.post("/api/skills/{item_id}/relations", status_code=status.HTTP_201_CREATED, tags=["Skills"])
def add_skill_relation_api(item_id: int, payload: RelationCreate):
    from core.skills import add_skill_relation
    add_skill_relation(item_id, payload.child_id, payload.relation_type, payload.relation_alias)
    return {"detail": "Relation added successfully."}

@app.delete("/api/skills/{item_id}/relations", tags=["Skills"])
def delete_skill_relation_api(item_id: int, payload: RelationCreate):
    from core.skills import remove_skill_relation
    remove_skill_relation(item_id, payload.child_id, payload.relation_type, payload.relation_alias)
    return {"detail": "Relation deleted successfully."}

@app.put("/api/skills/{item_id}/relations", tags=["Skills"])
def update_skill_relation_api(item_id: int, payload: RelationUpdate):
    from core.skills import update_skill_relation
    update_skill_relation(item_id, payload.child_id, payload.old_type, payload.old_alias, payload.new_type, payload.new_alias)
    return {"detail": "Relation updated successfully."}


# ==========================================
# RULES ENDPOINTS
# ==========================================
@app.get("/api/rules", response_model=List[AssetResponse], tags=["Rules"])
def list_rules():
    return [AssetResponse.from_db(item) for item in get_rules()]

@app.get("/api/rules/{item_id}", response_model=AssetResponse, tags=["Rules"])
def read_rule(item_id: int):
    return AssetResponse.from_db(get_rule_by_id(item_id))

@app.post("/api/rules", response_model=AssetResponse, status_code=status.HTTP_201_CREATED, tags=["Rules"])
def add_rule(payload: AssetCreate):
    file_blob = decode_base64_file(payload.file_content_base64) if payload.file_content_base64 else None
    new_id = create_rule(
        name=payload.name,
        storage_type=payload.storage_type,
        content=payload.content,
        file_blob=file_blob,
        file_name=payload.file_name,
        description=payload.description,
        tags=payload.tags,
        reference_url=payload.reference_url or ""
    )
    return AssetResponse.from_db(get_rule_by_id(new_id))

@app.put("/api/rules/{item_id}", response_model=AssetResponse, tags=["Rules"])
def edit_rule(item_id: int, payload: AssetUpdate):
    file_blob = decode_base64_file(payload.file_content_base64) if payload.file_content_base64 else None
    update_rule(
        item_id=item_id,
        name=payload.name,
        content=payload.content,
        description=payload.description,
        tags=payload.tags,
        reference_url=payload.reference_url or "",
        file_blob=file_blob,
        file_name=payload.file_name
    )
    return AssetResponse.from_db(get_rule_by_id(item_id))

@app.delete("/api/rules/{item_id}", tags=["Rules"])
def remove_rule(item_id: int):
    delete_rule(item_id)
    return {"detail": f"Successfully deleted rule with ID {item_id}"}

@app.get("/api/rules/{item_id}/download", tags=["Rules"])
def download_rule_file(item_id: int):
    item = get_rule_by_id(item_id)
    if item["type"] != "Real File Upload" or not item["file_blob"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This asset does not contain an uploaded file blob.")
    return Response(
        content=item["file_blob"],
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={item['file_name']}"}
    )

@app.get("/api/rules/{item_id}/relations", response_model=List[RelationResponse], tags=["Rules"])
def get_rule_relations_api(item_id: int):
    from core.rules import get_rule_relations
    relations = get_rule_relations(item_id)
    return [RelationResponse.from_db_row(r) for r in relations]

@app.post("/api/rules/{item_id}/relations", status_code=status.HTTP_201_CREATED, tags=["Rules"])
def add_rule_relation_api(item_id: int, payload: RelationCreate):
    from core.rules import add_rule_relation
    add_rule_relation(item_id, payload.child_id, payload.relation_type, payload.relation_alias)
    return {"detail": "Relation added successfully."}

@app.delete("/api/rules/{item_id}/relations", tags=["Rules"])
def delete_rule_relation_api(item_id: int, payload: RelationCreate):
    from core.rules import remove_rule_relation
    remove_rule_relation(item_id, payload.child_id, payload.relation_type, payload.relation_alias)
    return {"detail": "Relation deleted successfully."}

@app.put("/api/rules/{item_id}/relations", tags=["Rules"])
def update_rule_relation_api(item_id: int, payload: RelationUpdate):
    from core.rules import update_rule_relation
    update_rule_relation(item_id, payload.child_id, payload.old_type, payload.old_alias, payload.new_type, payload.new_alias)
    return {"detail": "Relation updated successfully."}


# ==========================================
# WORKFLOWS ENDPOINTS
# ==========================================
@app.get("/api/workflows", response_model=List[AssetResponse], tags=["Workflows"])
def list_workflows():
    return [AssetResponse.from_db(item) for item in get_workflows()]

@app.get("/api/workflows/{item_id}", response_model=AssetResponse, tags=["Workflows"])
def read_workflow(item_id: int):
    return AssetResponse.from_db(get_workflow_by_id(item_id))

@app.post("/api/workflows", response_model=AssetResponse, status_code=status.HTTP_201_CREATED, tags=["Workflows"])
def add_workflow(payload: WorkflowCreate):
    new_id = create_workflow(
        name=payload.name,
        content=payload.content,
        description=payload.description,
        tags=payload.tags
    )
    return AssetResponse.from_db(get_workflow_by_id(new_id))

@app.put("/api/workflows/{item_id}", response_model=AssetResponse, tags=["Workflows"])
def edit_workflow(item_id: int, payload: WorkflowUpdate):
    update_workflow(
        item_id=item_id,
        name=payload.name,
        content=payload.content,
        description=payload.description,
        tags=payload.tags
    )
    return AssetResponse.from_db(get_workflow_by_id(item_id))

@app.delete("/api/workflows/{item_id}", tags=["Workflows"])
def remove_workflow(item_id: int):
    delete_workflow(item_id)
    return {"detail": f"Successfully deleted workflow with ID {item_id}"}


# ==========================================
# MCP SERVICES ENDPOINTS
# ==========================================
@app.get("/api/mcp", response_model=List[AssetResponse], tags=["MCP Services"])
def list_mcps():
    return [AssetResponse.from_db(item) for item in get_mcps()]

@app.get("/api/mcp/{item_id}", response_model=AssetResponse, tags=["MCP Services"])
def read_mcp(item_id: int):
    return AssetResponse.from_db(get_mcp_by_id(item_id))

@app.post("/api/mcp", response_model=AssetResponse, status_code=status.HTTP_201_CREATED, tags=["MCP Services"])
def add_mcp(payload: AssetCreate):
    file_blob = decode_base64_file(payload.file_content_base64) if payload.file_content_base64 else None
    new_id = create_mcp(
        name=payload.name,
        storage_type=payload.storage_type,
        content=payload.content,
        file_blob=file_blob,
        file_name=payload.file_name,
        description=payload.description,
        tags=payload.tags,
        reference_url=payload.reference_url or ""
    )
    return AssetResponse.from_db(get_mcp_by_id(new_id))

@app.put("/api/mcp/{item_id}", response_model=AssetResponse, tags=["MCP Services"])
def edit_mcp(item_id: int, payload: AssetUpdate):
    file_blob = decode_base64_file(payload.file_content_base64) if payload.file_content_base64 else None
    update_mcp(
        item_id=item_id,
        name=payload.name,
        storage_type=payload.storage_type or "JSON Config",
        content=payload.content,
        description=payload.description,
        tags=payload.tags,
        reference_url=payload.reference_url or "",
        file_blob=file_blob,
        file_name=payload.file_name
    )
    return AssetResponse.from_db(get_mcp_by_id(item_id))

@app.delete("/api/mcp/{item_id}", tags=["MCP Services"])
def remove_mcp(item_id: int):
    delete_mcp(item_id)
    return {"detail": f"Successfully deleted MCP service with ID {item_id}"}

@app.get("/api/mcp/{item_id}/download", tags=["MCP Services"])
def download_mcp_file(item_id: int):
    item = get_mcp_by_id(item_id)
    if item["type"] != "Real File Upload" or not item["file_blob"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This asset does not contain an uploaded file blob.")
    return Response(
        content=item["file_blob"],
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={item['file_name']}"}
    )


# ==========================================
# EXPORTER ENDPOINT
# ==========================================
@app.post("/api/exporter/run", tags=["Exporter"])
def run_exporter(payload: ExportRequest):
    items_to_export = []
    for item_id in payload.selected_ids:
        # Fetch customization and verify it exists
        item = get_customization_by_id(item_id)
        if not item:
            raise AssetNotFoundError(f"Asset with ID {item_id} not found.")
        if item["type"] == "Web Bookmark":
            continue  # Web Bookmarks are not exportable
        items_to_export.append(item)
        
    exported_paths = export_assets(items_to_export, payload.base_path)
    return {"detail": "Export completed successfully.", "exported_files": exported_paths}
