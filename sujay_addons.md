# 🛠️ Sujay Addons & Reference Guide

This file tracks the project credentials, workspace modifications, and reference commands for **Ideation GOAT**.

---

## 👤 Git Configuration
The local Git credentials for this repository have been configured as follows:
* **Username:** `seeramsujay`
* **Email:** `sujayat2007@gmail.com`

---

## 🏗️ Architectural Transition Reference
The project has shifted from a visual Streamlit application to a pure **Model Context Protocol (MCP) Server** running over standard input/output (`stdio`).

### 📦 Files Reorganized
* **`server.py`**: The active entrypoint of the Ideation GOAT MCP server.
* **`app.py`**: Deleted (Streamlit UI components discarded).
* **`mcp_server.py`** $\rightarrow$ `Archives/mcp_server_v1.py`: Archived the original local indexing MCP server.

---

## 🤖 Active MCP Tools Reference

### 1. `search_knowledge_grid`
* **Purpose**: Query the multi-domain knowledge grid (GitHub, arXiv, patents, etc.).
* **Modes**:
  * `target`: Performs direct domain matches (e.g. computer science database optimization).
  * `discovery`: Bypasses the nearest domain cluster to find cross-domain structural parallels (e.g., matching cache eviction dynamics to biological cephalopod synapses).
* **Parameters**:
  * `query` (str): Search intent.
  * `mode` (str): `"target"` or `"discovery"`.
  * `cognitive_distance` (float): Force factor between `0.0` and `1.0`.

### 2. `breed_concepts`
* **Purpose**: Cross-pollinates two distinct concepts into a blended technical paradigm payload.
* **Parameters**:
  * `concept_a` (dict): Title, description, and domain context.
  * `concept_b` (dict): Title, description, and domain context.

### 3. `assess_viability`
* **Purpose**: Performs legal patent viability mapping. Returns the semantic vector gaps to safely route code implementation around active intellectual property conflicts.
* **Parameters**:
  * `system_design` (str): High-level system design text.

### 4. `generate_scaffolding_doc`
* **Purpose**: Translates conceptual synthesis payloads into a structured systems architecture handoff markdown specification complete with mathematical equations and **Mermaid.js** topology flowcharts.
* **Parameters**:
  * `synthesis_output` (dict): Output payload from `breed_concepts`.

---

## 🚀 Running the Server Locally

Verify dependencies are installed:
```bash
pip install -r requirements.txt
```

Launch the MCP server in `stdio` mode:
```bash
python server.py
```
