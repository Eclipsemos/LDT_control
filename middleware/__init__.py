"""
LDT MAVLink Gateway
Middleware to convert MAVLink messages to WebSocket JSON
"""

__version__ = "1.0.0"
__author__ = "LDT Team"

from .mavlink_gateway import MAVLinkGateway
from .config import Config

__all__ = ['MAVLinkGateway', 'Config']

