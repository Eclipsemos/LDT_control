"""
WebSocket Test Client for MAVLink Gateway
Simple client to test the MAVLink to WebSocket gateway
"""
import asyncio
import json
import sys
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Error: websockets library not installed")
    print("Install with: pip install websockets")
    sys.exit(1)


class TestClient:
    """Simple WebSocket test client"""
    
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.message_count = 0
        self.message_types = {}
        
    async def connect(self):
        """Connect to WebSocket server and receive messages"""
        print(f"Connecting to {self.uri}...")
        
        try:
            async with websockets.connect(self.uri) as websocket:
                print(f"✓ Connected to MAVLink Gateway\n")
                
                # Send initial request for drone state
                await websocket.send(json.dumps({"type": "GET_STATE"}))
                print("→ Requested initial drone state\n")
                
                # Receive messages
                async for message in websocket:
                    self.handle_message(message)
                    
        except websockets.exceptions.ConnectionRefused:
            print(f"✗ Connection refused. Is the gateway running on {self.uri}?")
        except KeyboardInterrupt:
            print("\n\nDisconnecting...")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def handle_message(self, message_str: str):
        """Handle received message"""
        try:
            message = json.loads(message_str)
            msg_type = message.get('type', 'UNKNOWN')
            timestamp = message.get('timestamp', '')
            data = message.get('data', {})
            
            # Count messages by type
            self.message_count += 1
            self.message_types[msg_type] = self.message_types.get(msg_type, 0) + 1
            
            # Display message based on type
            if msg_type == 'DRONE_STATE':
                self.display_drone_state(data)
            elif msg_type == 'HEARTBEAT':
                self.display_heartbeat(data)
            elif msg_type == 'GLOBAL_POSITION_INT':
                self.display_position(data)
            elif msg_type == 'ATTITUDE':
                self.display_attitude(data)
            elif msg_type == 'GPS_RAW_INT':
                self.display_gps(data)
            elif msg_type == 'BATTERY_STATUS':
                self.display_battery(data)
            else:
                # Show other messages in compact form
                print(f"[{timestamp}] {msg_type}")
            
            # Print summary every 100 messages
            if self.message_count % 100 == 0:
                self.print_summary()
                
        except json.JSONDecodeError:
            print(f"✗ Invalid JSON: {message_str[:100]}")
        except Exception as e:
            print(f"✗ Error handling message: {e}")
    
    def display_drone_state(self, data: dict):
        """Display aggregated drone state"""
        print("=" * 60)
        print("DRONE STATE SNAPSHOT")
        print("=" * 60)
        
        if 'position' in data:
            pos = data['position']
            print(f"Position:")
            print(f"  Lat/Lon: {pos.get('lat', 0):.6f}, {pos.get('lon', 0):.6f}")
            print(f"  Altitude: {pos.get('alt', 0):.1f}m (rel: {pos.get('relative_alt', 0):.1f}m)")
            print(f"  Velocity: vx={pos.get('vx', 0):.1f} vy={pos.get('vy', 0):.1f} vz={pos.get('vz', 0):.1f} m/s")
            print(f"  Heading: {pos.get('heading', 0):.1f}°")
        
        if 'attitude' in data:
            att = data['attitude']
            print(f"Attitude:")
            print(f"  Roll: {att.get('roll', 0):.3f} rad")
            print(f"  Pitch: {att.get('pitch', 0):.3f} rad")
            print(f"  Yaw: {att.get('yaw', 0):.3f} rad")
        
        if 'gps' in data:
            gps = data['gps']
            print(f"GPS:")
            print(f"  Fix Type: {gps.get('fix_type', 0)}")
            print(f"  Satellites: {gps.get('satellites_visible', 0)}")
        
        if 'battery' in data:
            bat = data['battery']
            print(f"Battery:")
            print(f"  Voltage: {bat.get('voltage', 0):.1f}V")
            if bat.get('current') is not None:
                print(f"  Current: {bat.get('current'):.1f}A")
            print(f"  Remaining: {bat.get('remaining', 0)}%")
        
        print("=" * 60)
        print()
    
    def display_heartbeat(self, data: dict):
        """Display heartbeat message"""
        status_map = {
            0: 'UNINIT',
            1: 'BOOT',
            2: 'CALIBRATING',
            3: 'STANDBY',
            4: 'ACTIVE',
            5: 'CRITICAL',
            6: 'EMERGENCY',
            7: 'POWEROFF',
            8: 'FLIGHT_TERMINATION'
        }
        status = status_map.get(data.get('system_status', 0), 'UNKNOWN')
        print(f"♥ HEARTBEAT - Status: {status}")
    
    def display_position(self, data: dict):
        """Display position message"""
        lat = data.get('lat', 0) / 1e7
        lon = data.get('lon', 0) / 1e7
        alt = data.get('alt', 0) / 1000.0
        rel_alt = data.get('relative_alt', 0) / 1000.0
        hdg = data.get('hdg', 0) / 100.0
        
        print(f"📍 POSITION - Lat: {lat:.6f}, Lon: {lon:.6f}, "
              f"Alt: {alt:.1f}m, Rel: {rel_alt:.1f}m, Hdg: {hdg:.1f}°")
    
    def display_attitude(self, data: dict):
        """Display attitude message"""
        roll = data.get('roll', 0)
        pitch = data.get('pitch', 0)
        yaw = data.get('yaw', 0)
        
        print(f"🎯 ATTITUDE - Roll: {roll:.3f}, Pitch: {pitch:.3f}, Yaw: {yaw:.3f} rad")
    
    def display_gps(self, data: dict):
        """Display GPS message"""
        lat = data.get('lat', 0) / 1e7
        lon = data.get('lon', 0) / 1e7
        alt = data.get('alt', 0) / 1000.0
        fix_type = data.get('fix_type', 0)
        sats = data.get('satellites_visible', 0)
        
        fix_names = {0: 'No Fix', 1: 'No Fix', 2: '2D', 3: '3D', 4: 'DGPS', 5: 'RTK Float', 6: 'RTK Fixed'}
        fix_name = fix_names.get(fix_type, f'Type {fix_type}')
        
        print(f"🛰️  GPS - Fix: {fix_name}, Sats: {sats}, "
              f"Pos: {lat:.6f}, {lon:.6f}, Alt: {alt:.1f}m")
    
    def display_battery(self, data: dict):
        """Display battery message"""
        voltages = data.get('voltages', [])
        voltage = voltages[0] / 1000.0 if voltages else 0
        current = data.get('current_battery', -1)
        remaining = data.get('battery_remaining', -1)
        
        print(f"🔋 BATTERY - Voltage: {voltage:.2f}V", end='')
        if current != -1:
            print(f", Current: {current / 100.0:.2f}A", end='')
        if remaining != -1:
            print(f", Remaining: {remaining}%", end='')
        print()
    
    def print_summary(self):
        """Print message statistics"""
        print("\n" + "-" * 60)
        print(f"Messages received: {self.message_count}")
        print("Message types:")
        for msg_type, count in sorted(self.message_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {msg_type}: {count}")
        print("-" * 60 + "\n")


async def main():
    """Main entry point"""
    # Parse command line arguments
    uri = "ws://localhost:8765"
    if len(sys.argv) > 1:
        uri = sys.argv[1]
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        MAVLink Gateway WebSocket Test Client              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    client = TestClient(uri)
    await client.connect()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✓ Test client stopped")

