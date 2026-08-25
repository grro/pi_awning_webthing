import asyncio
import logging
import threading
from typing import Protocol, cast, List, Dict
from fastmcp import FastMCP
from pydantic import AnyUrl, TypeAdapter
from datetime import datetime, timezone
from zeroconf import IPVersion, ServiceInfo, Zeroconf
import socket
from awning import Awning





class MDNS:

    def __init__(self):
        self.registered: Dict[str, ServiceInfo] = dict()
        self.zc = Zeroconf(ip_version=IPVersion.V4Only)
        self.service_type = "_mcp._tcp.local."
        self.hostname = socket.gethostname()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            self.local_ip = s.getsockname()[0]
        finally:
            s.close()


    def register_mdns(self, name: str, port: int):
        try:
            service_name = f"{name}.{self.service_type}"
            service_info = ServiceInfo(
                type_= self.service_type,
                name=service_name,
                addresses=[socket.inet_aton(self.local_ip)],
                port=port,
                properties={
                    "version": "1.0",
                    "path": "/sse",
                    "server_type": "fastmcp"
                },
                server=f"{self.hostname}.local.",
            )

            logging.info(f"mDNS: Registering {service_name} at {self.local_ip}:{port}")
            self.zc.register_service(service_info)
            self.registered[name] = service_info
        except Exception as e:
            logging.error(f"mDNS Registration failed: {e}")

    def unregister_mdns(self, name: str):
        service_info = self.registered.get(name)
        if service_info is not None:
            logging.info("mDNS: Unregistering service...")
            self.zc.unregister_service(service_info)
            self.zc.close()



class ResourceUpdateSession(Protocol):
    async def send_resource_updated(self, uri: AnyUrl) -> None:
        ...



class AwningMCPServer:

    def __init__(self, port: int, awnings: List[Awning], host: str = "0.0.0.0"):
        self.name = "Awning"
        self.host = host
        self.port = port

        self.mdns = MDNS()
        self.mcp = FastMCP(self.name)
        self.active_sessions: set[ResourceUpdateSession] = set()
        self.low_level_server = self.mcp._mcp_server
        self.awnings = awnings
        self.loop = asyncio.new_event_loop()

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


    async def __run(self) -> None:
        logging.info(f"MCP Server '{self.name}' running on http://{self.host}:{self.port}/sse")
        await self.mcp.run_async(
            transport="sse",
            host=self.host,
            port=self.port,
            uvicorn_config={"access_log": False, "log_config": None}
        )


    def start(self):
        self.mdns.register_mdns(self.name, self.port)

        def _run_loop():
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(self.__run())
            finally:
                self.loop.close()

        thread = threading.Thread(target=_run_loop, daemon=True)
        thread.start()


    def stop(self):
        self.mdns.unregister_mdns(self.name)
        self.loop.stop()
        logging.info("MCP Server stopped")