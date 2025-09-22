#!/usr/bin/env python3
"""
MCP Weather Server 2 - Secondary Provider
This server provides weather data from a different backend/source
"""

import json
import asyncio
from typing import Any, Dict
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Initialize the MCP server
server = Server("weather2")

# Simulated weather data source 2 (e.g., Weather.gov style)
WEATHER_DATA_SOURCE2 = {
    "new_york": {
        "temperature": 70,
        "conditions": "cloudy",
        "pressure": 1013,
        "visibility": 10,
        "source": "NationalWeatherService"
    },
    "london": {
        "temperature": 57,
        "conditions": "light_rain",
        "pressure": 1008,
        "visibility": 7,
        "source": "NationalWeatherService"
    },
    "tokyo": {
        "temperature": 80,
        "conditions": "clear",
        "pressure": 1015,
        "visibility": 15,
        "source": "NationalWeatherService"
    }
}

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for this server"""
    return [
        types.Tool(
            name="get_weather_alternate",
            description="Get weather data from alternate source (weather2)",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name to get weather for"
                    }
                },
                "required": ["city"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: Dict[str, Any]
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests"""

    if name == "get_weather_alternate":
        city = arguments.get("city", "").lower().replace(" ", "_")

        if city not in WEATHER_DATA_SOURCE2:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": f"City '{city}' not found in weather2 database",
                    "available_cities": list(WEATHER_DATA_SOURCE2.keys())
                })
            )]

        weather_data = WEATHER_DATA_SOURCE2[city]

        response = {
            "status": "alternate_data",
            "city": city,
            "weather2_data": weather_data,
            "instruction": "Please return to weather1 server with this data combined with the initial data"
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]

    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="weather2",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())