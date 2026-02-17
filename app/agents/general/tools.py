from settings import settings
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseConnectionParams


def getConversationsListTool():
    """
    Get the list of available conversations list tool.
    """
    tools = [];

    # mcp tools
    tools.append(
        MCPToolset(
            connection_params=SseConnectionParams(
                url=settings.MCP_SERVER
            ),
        )
    )


    return tools;