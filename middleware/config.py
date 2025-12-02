"""
Configuration module for MAVLink Gateway
"""
import os
from typing import Optional

class Config:
    """Configuration class for MAVLink to WebSocket gateway"""
    
    # MAVLink Connection
    # Use port 14551 to avoid conflict with QGroundControl (14550)
    MAVLINK_CONNECTION: str = os.getenv('MAVLINK_CONNECTION', 'udpin:0.0.0.0:14551')
    
    # WebSocket Server
    WEBSOCKET_HOST: str = os.getenv('WEBSOCKET_HOST', '0.0.0.0')
    WEBSOCKET_PORT: int = int(os.getenv('WEBSOCKET_PORT', '8765'))
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # MAVLink message filter (empty list means all messages)
    # Example: ['HEARTBEAT', 'GPS_RAW_INT', 'ATTITUDE', 'GLOBAL_POSITION_INT']
    # Add 'ODOMETRY' to filter if you see warnings about unsupported estimator types
    MESSAGE_FILTER: list = []
    
    # Messages to ignore/skip (useful for problematic message types)
    MESSAGE_IGNORE: list = []  # Example: ['ODOMETRY'] to skip odometry messages
    
    # Update rate limiting (messages per second, 0 = no limit)
    MAX_MESSAGE_RATE: int = 500
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None):
        """Load configuration from environment file"""
        if env_file and os.path.exists(env_file):
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except ImportError:
                pass
        return cls()

