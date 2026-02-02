from settings import settings
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseConnectionParams


def getMentalHealthTools():
    """
    Get the list of available mental health tools.
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