from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
import os
import json
import traceback
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

from app.utils.files import save_upload_file_tmp

app = FastAPI(title="Enterprise Workflow: Doc → Stories")

UNIFIED_AGENT_PATH = "app/mcp_servers/unified_agent.py"
params = StdioServerParameters(command="python", args=[UNIFIED_AGENT_PATH])

async def run_mcp_task(file_path: str, file_type: str) -> dict:
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            print("Client session started")
            await session.initialize()
            print("Session initialized")

            mcp_tools = await load_mcp_tools(session)
            tool_dict = {tool.name: tool for tool in mcp_tools}
            print("Tools loaded:", list(tool_dict.keys()))

            # Step 1: Parse document
            vector_id = await tool_dict["parse_document"].ainvoke({
                "file_path": file_path,
                "file_type": file_type
            })

            # Step 2: Extract features
            features = await tool_dict["extract_testable_features"].ainvoke({
                "vector_id": vector_id
            })
            print("Extracted Features:\n", features)

            # Step 3: Generate user stories
            stories: dict = await tool_dict["generate_user_stories"].ainvoke({
                "features": features
            })

            print("Extracted stories:\n", stories)

            #Step 4: Create epic + stories in Jira
            jira_response = await tool_dict["create_jira_story"].ainvoke({
                "story_block": stories
            })
            jira_response = json.loads(jira_response)

            # Step 5: Generate test cases for stories
            test_cases = await tool_dict["generate_test_cases"].ainvoke({
                "story_block": stories
            })
            test_cases = json.loads(test_cases)

            # Step 6: Create test cases in Jira
            test_case_creation_result = await tool_dict["create_jira_testcases"].ainvoke({
                    "epic_key": jira_response["epic_key"],
                    "stories_created": jira_response["stories_created"],
                    "test_cases": test_cases
                })
            test_case_creation_result = json.loads(test_case_creation_result)
            return {
                "jira_issues": jira_response,
                "test_cases": test_cases,
                "test_cases_jira": test_case_creation_result
            }


@app.post("/upload")
async def process_document(file: UploadFile = File(...)):
    file_path = None

    if not os.path.exists(UNIFIED_AGENT_PATH):
        raise HTTPException(status_code=500, detail=f"MCP agent script not found at {UNIFIED_AGENT_PATH}")

    try:
        if not file.filename.endswith((".pdf", ".docx")):
            raise HTTPException(status_code=400, detail="Only PDF or DOCX files are supported.")

        file_path = save_upload_file_tmp(file)
        file_type = "pdf" if file.filename.endswith(".pdf") else "docx"

        jira_response = await run_mcp_task(file_path, file_type)

        return {
            "message": "Successfully processed document and created issues in Jira.",
            "result": jira_response
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
