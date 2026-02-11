from typing import List
from mcplib.server import MCPServer
from awning import Awning



class AwningMCPServer(MCPServer):

    def __init__(self, port: int, awnings: List[Awning]):
        super().__init__("sunblind", port)
        self.awnings = awnings


        @self.mcp.tool()
        def set_position(name: str, position: int) -> str:
            """
            Sets the position of one or all sunblinds.
            :param name: The name of the blind or 'all'.
            :param position: 0 (fully open) to 100 (fully closed).
            """
            if name.lower() == "all":
                for a in self.awnings:
                    a.set_position(position)
                return f"Success: All sunblinds are moving to {position}%."

            awning = next((a for a in self.awnings if a.name == name), None)
            if awning is None:
                return f"Error: Sunblind '{name}' not found. Available: {[s.name for s in self.awnings]}"

            if not (0 <= position <= 100):
                return "Error: Position must be between 0 (open) and 100 (closed)."

            awning.set_position(position)
            return f"Success: {name} is moving to {position}%."

        @self.mcp.tool()
        def get_system_status() -> str:
            """Returns the current position of all registered sunblinds."""
            status_list = [f"{a.name}: {a.get_position()}%" for a in self.awnings]
            return "Current Status: " + " | ".join(status_list)

