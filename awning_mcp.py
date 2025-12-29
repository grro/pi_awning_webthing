from typing import List
from mcp_server import MCPServer
from awning import Awning


class AwningMCPServer(MCPServer):

    def __init__(self, name: str, port: int, awnings: List[Awning]):
        super().__init__(name, port)
        self.awnings = awnings


        @self.mcp.resource("awning://list/names")
        def list_awning_names() -> str:
            """Returns a comma-separated list of all available awning names."""
            return ", ".join([awning.name for awning in self.awnings])


        @self.mcp.resource("awning://{awningname}/position")
        def get_position(awningname: str) -> int:
            """
            Returns the current position of a specific awning.
            0 = fully open, 100 = fully closed.
            """
            for awning  in self.awnings:
                if awning.name == awningname:
                    return awning.get_position()
            raise ValueError(f"roller shutter '{name}' not found")


        @self.mcp.tool()
        def set_position(name: str, position: int) -> str:
            """
            Moves a specific awning to a target position.
            :param name: The name of the awning (e.g., 'Lane1')
            :param position: Target position from 0 (open) to 100 (closed)
            """
            awning = next((s for s in self.awnings if s.name == name), None)
            if awning is None:
                return f"Error: awning '{name}' was not found."

            if not (0 <= position <= 100):
                return "Error: Position must be an integer between 0 and 100."

            # Execute the movement
            awning.set_position(position)
            return f"Success: {name} is moving to {position}%."


# npx @modelcontextprotocol/inspector

