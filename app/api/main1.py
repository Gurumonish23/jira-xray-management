from fastapi import FastAPI, UploadFile, File, HTTPException
from ..utils.files import save_upload_file_tmp
from app.agents.langchain_agent import MCPAgentOrchestrator
from typing import List
import os
import traceback

app = FastAPI(title="Enterprise Workflow: Doc → Stories")

MCP_SERVERS = {
    "ingestion": "app/mcp_servers/ingestion_agent.py",
    "analysis": "app/mcp_servers/requirement_analysis_agent.py",
    "storygen": "app/mcp_servers/user_stories_generator_agent.py"
}

@app.post("/upload")
async def process_document(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith((".pdf", ".docx")):
            raise HTTPException(status_code=400, detail="Only PDF or DOCX files are supported.")

        file_path = save_upload_file_tmp(file)
        file_type = "pdf" if file.filename.endswith(".pdf") else "docx"

        orchestrator = MCPAgentOrchestrator(server_map=MCP_SERVERS)

        # Step 1: Ingest document
        chunks: List[str] = await orchestrator.call_ingestion_agent(file_path=file_path, file_type=file_type)

        # Step 2: Analyze to extract features
        features: str = await orchestrator.call_analysis_agent(chunks=chunks)

        # Step 3: Generate user stories
        stories: List[dict] = await orchestrator.call_storygen_agent(features=features)

        # Step 4: Push stories to Jira
        jira_responses = await orchestrator.push_stories_to_jira(stories)

        return {"message": "Successfully processed and pushed stories to Jira", "jira_issues": jira_responses}

    except Exception as e:
        traceback.print_exc()  # Log full stack trace in terminal
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
