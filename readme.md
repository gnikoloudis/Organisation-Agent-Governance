# Asset Management System

This repository contains a modular Streamlit-based application designed to manage, organize, and track various technical assets including Skills, Rules, Workflows, and MCP (Model Context Protocol) services.

## Overview

The system provides a unified interface to store assets using three different storage types: **Markdown Text**, **Real File Uploads**, and **Web Bookmarks**. It is built for extensibility, allowing users to categorize assets, add metadata, and manage configurations for different agent-based tools.

## Key Features

* **Modular Architecture**: Separate modules for Skills, Rules, Workflows, and MCP Services ensure code maintainability.

* **Dynamic Metadata Parsing**: Automatically extracts names, descriptions, and tags from YAML frontmatter within Markdown files or fetched URLs.
**Cross-Asset Synchronization**: When editing or saving assets, the system synchronizes metadata between the Markdown frontmatter and the database fields.

* **Flexible Storage**:
**Markdown Text**: Built-in editor with remote URL fetching capabilities.
**Real File Upload**: Secure file handling for `.md`, `.txt`, `.py`, `.csv`, and `.json` types.
**Web Bookmarks**: Quick access links for external documentation and complex configurations.
**Schema Validation**: MCP services include JSON schema validation to ensure configurations meet required protocols.


## Module Breakdown

| Module | Description |
| --- | --- |
| `skills.py` | Manages agent skills and instruction sets. |
| `rules.py` | Manages system rules with support for `@filename` path references.
| `workflows.py` | Simplified management for external configuration links. |
| `mcp.py` | Dedicated interface for MCP Server configurations with schema validation.
| `base_ui.py` | Provides helper functions for rendering the standard workspace UI.

## Getting Started

1. **Requirements**: Ensure you have `streamlit` and `jsonschema` installed, along with a functional `database/db_manager.py` module to handle CRUD operations.


2. **Running the App**:
```bash
streamlit run app.py

```


*(Note: Ensure your `app.py` or main entry point correctly imports and calls the `render()` functions from the modules.)*

## Usage Tips

* **YAML Frontmatter**: Use the following format at the top of your markdown files to auto-populate metadata:
```yaml
---
title: Your Asset Name
category: tag1, tag2
description: A comprehensive description of your asset.
---

```


* **Path Resolving**: In the **Rules** module, you can reference other files using `@filename` (relative) or `@/path/to/file.md` (absolute from root).


* **MCP Configs**: Ensure your JSON objects include the `mcpServers` key to pass validation requirements.