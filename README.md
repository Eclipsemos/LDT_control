# LDT Drone Application

Real-time drone control and visualization platform with MAVLink gateway middleware.

## Architecture

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   FRONTEND   │◄────────┤  MIDDLEWARE  │────────►│   BACKEND    │
│              │         │   (Done)     │         │   (To-Do)    │
│  • 3D Map    │         │  MAVLink ←→  │         │  • User      │
│  • Drone     │         │  WebSocket   │         │    Control   │
│    Model     │         │  Gateway     │         │  • 51Worlds  │
│  • 51 Worlds │         │              │         │    API       │
└──────────────┘         └──────────────┘         └──────────────┘
  (To-Do)                       ▲                    (To-Do)
       │                        │                        │
    WebSocket              MAVLink/WS              WebSocket/API
       │                        │                        │
       │                 ┌──────────────┐                │
       └─────────────────┤  PX4 Drone   │────────────────┘
                         │ QGroundCtrl  │
                         └──────────────┘
```

## Components

### Middleware (Implemented)
**MAVLink to WebSocket Gateway** - Converts PX4/QGroundControl MAVLink telemetry to JSON over WebSocket

**Features:**
- MAVLink connection support (UDP/TCP/Serial)
- Real-time message conversion to JSON
- Multiple WebSocket client support
- Drone state caching (position, attitude, battery, GPS)
- Message filtering and rate limiting
- Low latency (< 10ms)

**Location:** `middleware/`

### Frontend (To-Do)
React/Vue.js + Three.js for 3D drone visualization with 51 Worlds map integration

### Backend (To-Do)
Node.js/Python server for user commands and 51 Worlds API integration

---

## Quick Start - Middleware

### Prerequisites
- Python 3.8+
- PX4 SITL or physical drone with MAVLink
- QGroundControl (optional)

### Installation

```bash
cd middleware
pip install -r requirements.txt
```

### Run

**Option 1: Direct**
```bash
python mavlink_gateway.py
```

**Option 2: Startup Scripts**
```bash
# Windows
start_gateway.bat

# Linux/Mac
chmod +x start_gateway.sh
./start_gateway.sh
```

### Test

**Python Client:**
```bash
python test_client.py
```

**Web Client:**
Open `web_client_example.html` in your browser, click "Connect"

---

## Testing with PX4 SITL

**Terminal 1 - Start PX4 SITL:**

```bash
cd ~/PX4-Autopilot
make px4_sitl gazebo
```

**Terminal 2 - Run Gateway:**
```bash
cd middleware
python mavlink_gateway.py
```

**Terminal 3 - Test Client:**
```bash
python test_client.py
```

You should see real-time telemetry data flowing!

---

## Configuration

### Environment Variables

Create `.env` file in `middleware/` directory:

```env
MAVLINK_CONNECTION=udpin:0.0.0.0:14550
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8765
LOG_LEVEL=INFO
```

### MAVLink Connection Types

| Type | Example | Description |
|------|---------|-------------|
| UDP Listen | `udpin:0.0.0.0:14550` | Listen for incoming (default, for SITL/QGC) |
| UDP Connect | `udpout:127.0.0.1:14550` | Connect to specific endpoint |
| TCP | `tcp:127.0.0.1:5760` | TCP connection |
| Serial (Windows) | `COM3` | Serial port |
| Serial (Linux) | `/dev/ttyUSB0` | Serial port |
| Serial + Baud | `/dev/ttyUSB0:57600` | Custom baud rate |

### Message Filtering

Edit `middleware/config.py`:

```python
MESSAGE_FILTER = [
    'HEARTBEAT',
    'GPS_RAW_INT',
    'GLOBAL_POSITION_INT',
    'ATTITUDE',
    'BATTERY_STATUS'
]
```

Leave empty `[]` to receive all messages.

### Rate Limiting

```python
MAX_MESSAGE_RATE = 50  # messages per second, 0 = no limit
```

---

## WebSocket API

### Connection
```
ws://localhost:8765
```

### Message Format
All messages are JSON:

```json
{
  "type": "MESSAGE_TYPE",
  "timestamp": "2025-12-01T10:30:00.123456",
  "data": { ... }
}
```

### Key Message Types

| Type | Description | Rate |
|------|-------------|------|
| `HEARTBEAT` | System status | 1 Hz |
| `GLOBAL_POSITION_INT` | Position, altitude, velocity | 5 Hz |
| `ATTITUDE` | Roll, pitch, yaw | 10-50 Hz |
| `GPS_RAW_INT` | Raw GPS data | 5 Hz |
| `BATTERY_STATUS` | Battery info | 1 Hz |
| `DRONE_STATE` | Aggregated state (sent on connect) | On request |

### Example Messages

**Position:**
```json
{
  "type": "GLOBAL_POSITION_INT",
  "timestamp": "2025-12-01T10:30:00.123456",
  "data": {
    "lat": 473977418,      // Latitude * 1e7
    "lon": 85455939,       // Longitude * 1e7
    "alt": 48800,          // Altitude (mm)
    "relative_alt": 1200,  // Relative altitude (mm)
    "vx": 0,               // Velocity X (cm/s)
    "vy": 0,               // Velocity Y (cm/s)
    "vz": 0,               // Velocity Z (cm/s)
    "hdg": 18000           // Heading * 100
  }
}
```

**Attitude:**
```json
{
  "type": "ATTITUDE",
  "timestamp": "2025-12-01T10:30:00.123456",
  "data": {
    "roll": 0.01,
    "pitch": -0.02,
    "yaw": 3.14,
    "rollspeed": 0.0,
    "pitchspeed": 0.0,
    "yawspeed": 0.0
  }
}
```

**Drone State (Aggregated):**
```json
{
  "type": "DRONE_STATE",
  "timestamp": "2025-12-01T10:30:00.123456",
  "data": {
    "position": {
      "lat": 47.3977418,
      "lon": 8.5455939,
      "alt": 48.8,
      "relative_alt": 1.2,
      "vx": 0.0,
      "vy": 0.0,
      "vz": 0.0,
      "heading": 180.0
    },
    "attitude": {
      "roll": 0.01,
      "pitch": -0.02,
      "yaw": 3.14
    },
    "battery": {
      "voltage": 12.6,
      "current": 5.2,
      "remaining": 85
    },
    "gps": {
      "fix_type": 3,
      "satellites_visible": 12
    }
  }
}
```

### Client Requests

**Get Current State:**
```json
{"type": "GET_STATE"}
```

**Ping:**
```json
{"type": "PING"}
```

Response:
```json
{"type": "PONG", "timestamp": "2025-12-01T10:30:00.123456"}
```

---

## Client Integration Examples

### JavaScript

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
  console.log('Connected!');
  ws.send(JSON.stringify({ type: 'GET_STATE' }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.type === 'GLOBAL_POSITION_INT') {
    const lat = msg.data.lat / 1e7;
    const lon = msg.data.lon / 1e7;
    const alt = msg.data.alt / 1000.0;
    updateDronePosition(lat, lon, alt);
  }
  
  if (msg.type === 'ATTITUDE') {
    updateDroneOrientation(msg.data.roll, msg.data.pitch, msg.data.yaw);
  }
};
```

### Python

```python
import asyncio
import websockets
import json

async def listen():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as ws:
        # Request initial state
        await ws.send(json.dumps({"type": "GET_STATE"}))
        
        # Listen for messages
        async for message in ws:
            data = json.loads(message)
            print(f"{data['type']}: {data['data']}")

asyncio.run(listen())
```

---

## 🐛 Troubleshooting

### "Failed to connect to MAVLink"
- ✅ Verify PX4 SITL or QGroundControl is running
- ✅ Check firewall settings for port 14550
- ✅ Try `udpin:0.0.0.0:14550` (listening mode)
- ✅ Check connection string format

### "No messages received"
- ✅ Verify MAVLink source is sending data
- ✅ Check for UDP port blocking
- ✅ Look for errors in gateway logs
- ✅ Try increasing LOG_LEVEL to DEBUG

### "WebSocket connection refused"
- ✅ Ensure gateway is running
- ✅ Check WebSocket port (default 8765)
- ✅ Set `WEBSOCKET_HOST=0.0.0.0` to listen on all interfaces
- ✅ Check firewall settings

### Connection drops frequently
- ✅ Check network stability
- ✅ Enable rate limiting (set MAX_MESSAGE_RATE)
- ✅ Review client-side error handling
- ✅ Monitor system resources

---

## 📁 Project Structure

```
LDT_control/
├── middleware/                    # ✅ Middleware (Implemented)
│   ├── mavlink_gateway.py         # Main gateway service
│   ├── config.py                  # Configuration
│   ├── test_client.py             # CLI test client
│   ├── web_client_example.html    # Browser test client
│   ├── requirements.txt           # Dependencies
│   ├── start_gateway.bat          # Windows startup
│   ├── start_gateway.sh           # Linux/Mac startup
│   └── __init__.py
├── frontend/                      # 📋 To-Do
└── backend/                       # 📋 To-Do
```

---

## 🗺️ Roadmap

### ✅ Phase 1: Middleware (Complete)
- [x] MAVLink to WebSocket gateway
- [x] Message parsing and conversion
- [x] Multi-client support
- [x] Test clients
- [x] Documentation

### 📋 Phase 2: Frontend (Next)
- [ ] React/Vue.js setup
- [ ] Three.js 3D visualization
- [ ] WebSocket client integration
- [ ] 51 Worlds map integration
- [ ] UI/UX design

### 📋 Phase 3: Backend
- [ ] Server setup (Node.js/Python)
- [ ] WebSocket command server
- [ ] 51 Worlds API integration
- [ ] Authentication system
- [ ] Command validation

### 📋 Phase 4: Integration
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Production deployment

---

## 🔐 Security (For Production)

- [ ] Implement authentication (JWT/API keys)
- [ ] Use WSS (WebSocket Secure) with SSL/TLS
- [ ] Validate all commands before forwarding
- [ ] Implement geofencing
- [ ] Add rate limiting
- [ ] Enable audit logging
- [ ] Role-based access control

---

## 📚 Resources

- **MAVLink:** [mavlink.io](https://mavlink.io/)
- **pymavlink:** [pymavlink docs](https://mavlink.io/en/mavgen_python/)
- **PX4:** [px4.io](https://px4.io/)
- **PX4 SITL:** [docs.px4.io/main/en/simulation](https://docs.px4.io/main/en/simulation/)
- **WebSockets:** [developer.mozilla.org/en-US/docs/Web/API/WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- **51 Worlds:** [51.world](https://51.world/)

---

## 📝 License

Part of the LDT drone application system.

---

**Version 1.0.0** | December 2025

