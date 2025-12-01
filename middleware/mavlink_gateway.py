"""
MAVLink to WebSocket Gateway
Converts MAVLink messages from PX4/QGroundControl to WebSocket JSON messages
"""
import asyncio
import json
import logging
import time
from typing import Set, Dict, Any
from datetime import datetime

import websockets
from websockets.server import WebSocketServerProtocol
from pymavlink import mavutil

from config import Config


class MAVLinkGateway:
    """Gateway to convert MAVLink messages to WebSocket"""
    
    def __init__(self, config: Config):
        self.config = config
        self.clients: Set[WebSocketServerProtocol] = set()
        self.mavlink_connection = None
        self.logger = self._setup_logger()
        self.running = False
        self.message_count = 0
        self.last_rate_check = time.time()
        self.drone_state: Dict[str, Any] = {}
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('MAVLinkGateway')
        logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def connect_mavlink(self):
        """Establish MAVLink connection"""
        try:
            self.logger.info(f"Connecting to MAVLink: {self.config.MAVLINK_CONNECTION}")
            self.mavlink_connection = mavutil.mavlink_connection(
                self.config.MAVLINK_CONNECTION,
                source_system=255,
                source_component=0
            )
            self.logger.info("MAVLink connection established")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to MAVLink: {e}")
            return False
    
    def parse_mavlink_message(self, msg) -> Dict[str, Any]:
        """Convert MAVLink message to JSON-serializable dictionary"""
        try:
            msg_dict = msg.to_dict()
            
            # Add metadata
            result = {
                'type': msg.get_type(),
                'timestamp': datetime.utcnow().isoformat(),
                'data': msg_dict
            }
            
            # Update drone state cache for key messages
            self._update_drone_state(msg)
            
            return result
        except Exception as e:
            self.logger.error(f"Error parsing MAVLink message: {e}")
            return {}
    
    def _update_drone_state(self, msg):
        """Update internal drone state cache"""
        msg_type = msg.get_type()
        
        if msg_type == 'HEARTBEAT':
            self.drone_state['heartbeat'] = {
                'type': msg.type,
                'autopilot': msg.autopilot,
                'base_mode': msg.base_mode,
                'custom_mode': msg.custom_mode,
                'system_status': msg.system_status,
                'mavlink_version': msg.mavlink_version
            }
        
        elif msg_type == 'GPS_RAW_INT':
            self.drone_state['gps'] = {
                'lat': msg.lat / 1e7,
                'lon': msg.lon / 1e7,
                'alt': msg.alt / 1000.0,
                'fix_type': msg.fix_type,
                'satellites_visible': msg.satellites_visible
            }
        
        elif msg_type == 'GLOBAL_POSITION_INT':
            self.drone_state['position'] = {
                'lat': msg.lat / 1e7,
                'lon': msg.lon / 1e7,
                'alt': msg.alt / 1000.0,
                'relative_alt': msg.relative_alt / 1000.0,
                'vx': msg.vx / 100.0,
                'vy': msg.vy / 100.0,
                'vz': msg.vz / 100.0,
                'heading': msg.hdg / 100.0
            }
        
        elif msg_type == 'ATTITUDE':
            self.drone_state['attitude'] = {
                'roll': msg.roll,
                'pitch': msg.pitch,
                'yaw': msg.yaw,
                'rollspeed': msg.rollspeed,
                'pitchspeed': msg.pitchspeed,
                'yawspeed': msg.yawspeed
            }
        
        elif msg_type == 'BATTERY_STATUS':
            self.drone_state['battery'] = {
                'voltage': msg.voltages[0] / 1000.0 if msg.voltages else 0,
                'current': msg.current_battery / 100.0 if msg.current_battery != -1 else None,
                'remaining': msg.battery_remaining
            }
    
    async def mavlink_reader(self):
        """Read MAVLink messages in async loop"""
        self.logger.info("Starting MAVLink reader...")
        
        while self.running:
            try:
                # Non-blocking receive with timeout
                msg = self.mavlink_connection.recv_match(blocking=False, timeout=0.01)
                
                if msg:
                    # Filter messages if configured
                    if (self.config.MESSAGE_FILTER and 
                        msg.get_type() not in self.config.MESSAGE_FILTER):
                        continue
                    
                    # Parse and broadcast
                    parsed_msg = self.parse_mavlink_message(msg)
                    if parsed_msg:
                        await self.broadcast(parsed_msg)
                        self.message_count += 1
                
                # Yield control to event loop
                await asyncio.sleep(0.001)
                
                # Rate limiting check
                if self.config.MAX_MESSAGE_RATE > 0:
                    current_time = time.time()
                    elapsed = current_time - self.last_rate_check
                    if elapsed >= 1.0:
                        rate = self.message_count / elapsed
                        if rate > self.config.MAX_MESSAGE_RATE:
                            self.logger.warning(f"Message rate ({rate:.1f}/s) exceeds limit")
                        self.message_count = 0
                        self.last_rate_check = current_time
                        
            except Exception as e:
                self.logger.error(f"Error in MAVLink reader: {e}")
                await asyncio.sleep(0.1)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected WebSocket clients"""
        if not self.clients:
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                self.logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle WebSocket client connection"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.logger.info(f"Client connected: {client_id}")
        
        # Add client to set
        self.clients.add(websocket)
        
        try:
            # Send current drone state on connection
            if self.drone_state:
                await websocket.send(json.dumps({
                    'type': 'DRONE_STATE',
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': self.drone_state
                }))
            
            # Listen for client messages (for future control commands)
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self.logger.info(f"Received from client {client_id}: {data}")
                    
                    # Handle client requests
                    await self.handle_client_request(websocket, data)
                    
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid JSON from client {client_id}")
                except Exception as e:
                    self.logger.error(f"Error handling client message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client disconnected: {client_id}")
        finally:
            self.clients.discard(websocket)
    
    async def handle_client_request(self, websocket: WebSocketServerProtocol, request: Dict[str, Any]):
        """Handle specific client requests"""
        request_type = request.get('type', '')
        
        if request_type == 'GET_STATE':
            # Send current drone state
            await websocket.send(json.dumps({
                'type': 'DRONE_STATE',
                'timestamp': datetime.utcnow().isoformat(),
                'data': self.drone_state
            }))
        
        elif request_type == 'PING':
            # Respond to ping
            await websocket.send(json.dumps({
                'type': 'PONG',
                'timestamp': datetime.utcnow().isoformat()
            }))
        
        else:
            self.logger.warning(f"Unknown request type: {request_type}")
    
    async def start_websocket_server(self):
        """Start WebSocket server"""
        self.logger.info(
            f"Starting WebSocket server on {self.config.WEBSOCKET_HOST}:{self.config.WEBSOCKET_PORT}"
        )
        
        async with websockets.serve(
            self.handle_client,
            self.config.WEBSOCKET_HOST,
            self.config.WEBSOCKET_PORT
        ):
            await asyncio.Future()  # Run forever
    
    async def run(self):
        """Main run loop"""
        self.running = True
        
        # Connect to MAVLink
        if not self.connect_mavlink():
            self.logger.error("Failed to establish MAVLink connection")
            return
        
        # Start both tasks
        try:
            await asyncio.gather(
                self.mavlink_reader(),
                self.start_websocket_server()
            )
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
        finally:
            self.running = False
            if self.mavlink_connection:
                self.mavlink_connection.close()


async def main():
    """Main entry point"""
    config = Config()
    gateway = MAVLinkGateway(config)
    await gateway.run()


if __name__ == '__main__':
    asyncio.run(main())

