from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.tool import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List
from dotenv import load_dotenv

load_dotenv()

class MCPAgentOrchestrator:

    def __init__(self, server_map: dict):
        self.server_map = server_map
        self.model = ChatOpenAI(model="gpt-4o-mini")

    async def call_ingestion_agent(self, file_path: str, file_type: str) -> List[str]:
        print("call_ingestion_agent")
        print(self.server_map["ingestion"])
        params = StdioServerParameters(command="python", args=[self.server_map["ingestion"]])
        print(params)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                print("clientSession")
                await session.initialize()
                print("session")
                tools = await load_mcp_tools(session)
                print("tools")
                return await tools["parse_document"].ainvoke({
                    "file_path": file_path,
                    "file_type": file_type
                })

    async def call_analysis_agent(self, chunks: List[str]) -> str:
        params = StdioServerParameters(command="python", args=[self.server_map["analysis"]])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                return await tools["extract_testable_features"].ainvoke({
                    "text_chunks": chunks
                })

    async def call_storygen_agent(self, features: str) -> List[dict]:
        params = StdioServerParameters(command="python", args=[self.server_map["storygen"]])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                return await tools["generate_user_stories"].ainvoke({
                    "features": features
                })

    async def push_stories_to_jira(self, stories: List[dict]) -> List[dict]:
        params = StdioServerParameters(command="python", args=[self.server_map["storygen"]])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                return [
                    await tools["create_jira_story"].ainvoke({"story": story})
                    for story in stories
                ]
