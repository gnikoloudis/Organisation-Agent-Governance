# Asset Management System

This repository contains a modular Streamlit-based application and a FastAPI REST API designed to manage, organize, and track various technical assets including Skills, Rules, Workflows, and MCP (Model Context Protocol) services.

The codebase is built with a decoupled architecture, isolating the core business and validation logic from the presentation layer (Streamlit UI) and database engines (supporting SQLite locally and PostgreSQL/Supabase in the cloud).

---

## Architecture Overview

* **Core Logic (`core/`)**: Independent, pure-Python modules for managing assets, validating YAML frontmatter, running JSON schemas, and exporting files.
* **Service Layer (`services/`)**: A dynamic gateway layer that redirects all calls from the UI either to local core modules or over HTTP to the REST API, preventing UI code duplication.
* **Streamlit UI (`modules/` & `app.py`)**: A premium web dashboard for interactive, visual configuration.
* **REST API (`main_api.py`)**: A FastAPI server exposing CRUD endpoints for tools, integrations, or external agents.
* **Database Manager (`database/db_manager.py`)**: A unified wrapper handling SQLite or PostgreSQL connection routing and dialect translations dynamically.

---

## Configuration Variables

Configure the application behavior using the following environment variables:

| Environment Variable | Accepted Values | Default | Description |
|---|---|---|---|
| `DEPLOYMENT_ENV` | `local`, `cloud` | `local` | Set to `cloud` to connect to PostgreSQL/Supabase, or `local` for SQLite. |
| `DATABASE_URL` | Connection String | N/A | PostgreSQL URI (e.g. `postgresql://user:pass@host:port/dbname`). Required if `DEPLOYMENT_ENV=cloud`. |
| `AGENT_DB_PATH` | File Path | `agent_customizations.db` | File path for SQLite database. |
| `STREAMLIT_MODE` | `direct`, `api` | `direct` | Set to `api` to route Streamlit UI requests via HTTP to the REST API, or `direct` for direct database execution. |
| `API_BASE_URL` | URL | `http://127.0.0.1:8080` | Endpoint of the running FastAPI server. Required if `STREAMLIT_MODE=api`. |

---

## How to Run the Application

### 1. Working Locally (Default Mode)
In local mode, the application runs on a local SQLite database and executes database queries directly from the Streamlit UI.

#### Run Streamlit UI Dashboard:
```bash
.\.venv\Scripts\streamlit run app.py
```
*App is available at: `http://localhost:8501`*

---

### 2. Working Locally with Decoupled REST API
In this mode, Streamlit acts as a thin HTTP client, communicating with a running FastAPI backend server.

#### Step A: Run the FastAPI REST API Server:
```bash
.\.venv\Scripts\uvicorn main_api:app --host 127.0.0.1 --port 8080 --reload
```
*API docs (Swagger UI) are available at: `http://127.0.0.1:8080/docs`*

#### Step B: Run the Streamlit UI (pointing to the API):
* **In PowerShell**:
  ```powershell
  $env:STREAMLIT_MODE="api"
  .\.venv\Scripts\streamlit run app.py
  ```
* **In Command Prompt**:
  ```cmd
  set STREAMLIT_MODE=api
  .\.venv\Scripts\streamlit run app.py
  ```

---

### 3. Deploying / Working in the Cloud (Vercel + Supabase PostgreSQL)
To run the decoupled backend on Vercel, you must use a cloud database (like Supabase or Neon PostgreSQL) because Vercel Serverless functions are stateless and local SQLite files will not persist.

#### Step A: Set up your Cloud Database
Create a database instance on Supabase and obtain your Connection URI (`postgresql://...`).

#### Step B: Run/Deploy the REST API on Vercel
1. Set the following environment variables in your Vercel deployment:
   ```env
   DEPLOYMENT_ENV=cloud
   DATABASE_URL=postgresql://your-supabase-username:password@host:5432/postgres
   ```
2. Deploy the FastAPI app (`main_api.py`) as a serverless function. (The DB schema will automatically initialize on server start).

#### Step C: Run the Streamlit UI (Pointing to the Cloud API)
Run your Streamlit instance (deployed on Streamlit Community Cloud, Hugging Face, or locally) targeting your deployed Vercel API:

* **In PowerShell**:
  ```powershell
  $env:STREAMLIT_MODE="api"
  $env:API_BASE_URL="https://your-fastapi-app.vercel.app"
  .\.venv\Scripts\streamlit run app.py
  ```
* **In Command Prompt**:
  ```cmd
  set STREAMLIT_MODE=api
  set API_BASE_URL=https://your-fastapi-app.vercel.app
  .\.venv\Scripts\streamlit run app.py
  ```

---

## Skills & Rules Relations & Hierarchical Exporter

The system supports creating, managing, and exporting parent-child relationships between **Skills** and **Rules**.

### Features
* **Relation Mapping**: Link a parent Skill or Rule to other child Skills or Rules.
* **Relation Types**: Categorize relations as `"reference"`, `"asset"`, `"tool"`, `"resources"`, or `"scripts"`.
* **User-Defined Aliases**: Assign custom filenames/aliases (e.g. `utils.py`, `config.json`, `setup.sh`) to the related items.
* **Deletion Protection**: To preserve referential integrity, any customization that is currently referenced as a child in an active relationship cannot be deleted. Deleting a parent automatically cleans up its outgoing relations.
* **Hierarchical Exporting**: When you export a parent Skill or Rule, the Exporter automatically packages all linked children into structured subdirectories:
  - `base_path/skills/{parent_name}/references/{alias_name}`
  - `base_path/skills/{parent_name}/assets/{alias_name}`
  - `base_path/skills/{parent_name}/tools/{alias_name}`
  - `base_path/skills/{parent_name}/resources/{alias_name}`
  - `base_path/skills/{parent_name}/scripts/{alias_name}`
  - **Deduplicated Selection**: In the Exporter UI, only parent/root assets are selectable. Their child assets are listed nested underneath for user information. If a child asset is linked to any selected parent, the Exporter automatically skips exporting it at the root level to avoid duplicates, while still packaging it nested under the parent directory.
* **Relationship Management in View Tab**: In the Skills and Rules active lists, only root assets are displayed at the top level. The related items are nested underneath them in sub-cards. Under **Edit Relation Details**, you can preview, download, or edit the child asset itself, as well as change the relationship metadata (Type and Alias/Filename) directly from inside the parent.
* **Remote URL Imports**: Under the relationship panel, you can import new related items directly from remote URLs:
  - **Markdown (`.md`)**: Automatically fetches content and extracts frontmatter (`title`, `description`, `category`) to pre-fill metadata fields.
  - **Code Assets (e.g., `.py`, `.js`, `.json`)**: Fetches content as a raw file upload, prompting manual entry for name, description, and tags in the UI form.

---

## Running the Automated Test Suite

To verify CRUD operations, schema validation, database compatibility, and relations mapping:

```bash
.\.venv\Scripts\python -m pytest tests/test_api.py
```
*The test suite automatically isolates and wipes a temporary SQLite database (`test_agent_customizations.db`) to ensure tests do not affect your production database.*