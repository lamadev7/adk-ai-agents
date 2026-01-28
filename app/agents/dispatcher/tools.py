from google.adk.tools import FunctionTool, ToolContext
from app.constants.mockLoadJSON import mockLoads

async def getDispatcherLoads(
    tool_context: ToolContext,
    skip: int,
    limit: int,
    search: str,
):
    """
    Get the loads for the dispatcher.

    Args:
        skip: The number of loads to skip.
        limit: The number of loads to return.
        search: The search query to use for the request to search load.
    """
    
    try:
        # Access state from session via tool_context
        token = tool_context.state.get("token")
        user = tool_context.state.get("user")
        
        print(f"Token: {token}")
        print(f"User: {user}")
        
        loads = mockLoads

        if search:
            loads = [load for load in loads if search in load.get("reference_number")]

        if skip:
            loads = loads[skip:]

        if limit:
            loads = loads[:limit]

        return loads

    except Exception as e:
        print(f"Error getting loads: {e}")
        return []






# tools 
getDispatcherLoadsTool = FunctionTool(getDispatcherLoads)