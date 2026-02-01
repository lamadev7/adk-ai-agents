from google.adk.tools import FunctionTool, ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters


def getMentalHealthTools():
    """
    Get the list of available mental health tools.
    """
    tools = [];

    # mcp tools
    tools.append(
        MCPToolset(
            connection_params=StdioServerParameters(
                command="node",
                args=['/Users/bikram/Documents/projects/ai agents/mcp/dist/main.js']
            ),
        )
    )


    return tools;