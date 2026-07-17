# Future Steps

This document tracks upcoming phases and progress according to the project roadmap.

## Pending from Phase 1 & 2
- Run data ingestion locally to test parsing and chunking on real GitHub Data.
- Verify filtering works effectively in Streamlit UI using real data topics and tags.

## Phase 3: Cloud Infrastructure & Scaling
- Move vector database to a cloud solution (Pinecone / Supabase).
- Develop FastAPI backend for scalable API access.
- Optionally upgrade embedding model to OpenAI `text-embedding-3-small` or similar.

## Phase 4: Production Web App & LLM Synthesis
- Migrate frontend from Streamlit to Next.js + TailwindCSS.
- Introduce LLM integration (Gemini/GPT-4o) to summarize and explain the top matched frameworks.
- Setup a cron job for automated ingestion.

## Phase 5: Model Context Protocol (MCP) Server
- [x] Create a Python MCP server (`mcp_server.py`) using `FastMCP`.
- [x] Expose `search_repos` tool for semantic querying by AI clients.
- [x] Expose `ingest_repos` tool to trigger repo crawls for any language via the agent.
- [x] Expose `github-ideas://stats` resource to retrieve database sizes.
- [ ] Test the local integration on Claude Desktop.
- [ ] Migrate the stdio transport to HTTP SSE for network hosting.

