# IoT Fleet Monitor

A simulated industrial IoT monitoring system: sensor data flows through an MQTT broker into a Flask backend that stores readings, detects anomalies, and exposes them through a REST API and a live dashboard.

Built as a learning/portfolio project to practice distributed-systems patterns (pub/sub messaging), backend engineering, applied ML on streaming data, and DevOps practices (containerization, CI/CD).

## Architecture

```
┌─────────────┐      MQTT publish       ┌─────────────┐
│  Sensor      │  (JSON: sensor_id,      │             │
│  Simulator   │   type, value,          │   MQTT      │
│  (Python)    │   timestamp)            │   Broker    │
│              │ ───────────────────────▶│  (Mosquitto)│
└─────────────┘                          └──────┬──────┘
                                                 │ MQTT subscribe
                                                 ▼
                                          ┌─────────────┐
                                          │   Flask      │
                                          │   Backend    │
                                          │  - subscribes│
                                          │  - stores    │
                                          │  - detects   │
                                          │    anomalies │
                                          └──────┬──────┘
                                                 │
                                    ┌────────────┼────────────┐
                                    ▼                          ▼
                             ┌─────────────┐          ┌──────────────┐
                             │  Database    │          │  REST API    │
                             │  (SQLite→    │          │  endpoints   │
                             │  Postgres)   │          │  (/readings, │
                             └─────────────┘          │  /anomalies) │
                                                        └──────┬───────┘
                                                               │ HTTP GET
                                                               ▼
                                                        ┌──────────────┐
                                                        │  Dashboard    │
                                                        │  (Flask +     │
                                                        │  Chart.js)    │
                                                        └──────────────┘
```

## Design decisions

- **MQTT over direct HTTP calls from sensors**: decouples data producers from consumers. Sensors don't know or care who's listening, so the system can add new consumers (e.g. a logging service) without touching sensor code, and a backend outage doesn't take down data production.
- **Backend split into logical responsibilities**: (subscribe, store, detect) even while running as a single process initially — this keeps the door open to splitting into microservices later without a rewrite.
- **SQLite via SQLAlchemy ORM**: zero setup to start, but swapping to Postgres/openGauss later is a config change, not a rewrite.
- **The real numbers for anomaly detection**, validated via a standalone script against synthetic outliers: 9/10 detected, ~1% false positive rate.
- **Dashboard talks only to the REST API**, never the database directly, so the frontend can be replaced independently of the backend.

- **Using python Tags "worth the check"**: Base image shows known CVEs via Docker Scout at the time of writing; acceptable for a demo/learning project, would require base image hardening (distroless, or regular rebuilds) for production use.


## Tech stack

- **Sensors**: Python, `paho-mqtt`
- **Broker**: Mosquitto (MQTT)
- **Backend**: Flask, SQLAlchemy, scikit-learn (anomaly detection)
- **Dashboard**: Flask + Chart.js
- **Infra**: Docker, docker-compose
- **CI**: GitHub Actions (tests + linting)

## Project structure

```
iot-fleet-monitor/
├── sensors/
│   └── simulator.py
├── backend/
│   ├── app.py
│   ├── models.py
│   └── mqtt_listener.py
├── dashboard/
│   └── templates/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Status

🚧 Work in progress — following a structured build plan.

## Build progress

### Week 1 — Foundations & data pipeline
- [x] Repo structure + initial README
- [x] Local MQTT broker running via Docker (Mosquitto)
- [x] Sensor simulator publishing readings (temperature, vibration, occupancy)
- [x] Flask backend: MQTT listener
- [x] Flask backend: persistence layer (SQLAlchemy + SQLite)

### Week 2 — Reliability, anomaly detection, dashboard
- [x] MQTT disconnect/reconnect visibility
- [x] Health check endpoint reporting real pipeline status
- [x] Anomaly detection (threshold/z-score, then Isolation Forest)
- [x] Dashboard: live readings + historical trends
- [x] Dashboard: anomaly flags

### Week 3 — Hardening, DevOps, polish
- [x] Tests
- [ ] Dockerize full stack (docker-compose)
- [ ] GitHub Actions CI (tests + linting)
- [ ] Full documentation pass (setup guide, design rationale)
- [ ] Demo GIF/video + final polish

## Setup

**Prerequisites:** Python 3.12+, Docker Desktop

**1. Clone the repo and install dependencies**
```bash
git clone https://github.com/Xbalawi/iot-fleet-monitor.git
cd iot-fleet-monitor
pip install -r requirements.txt
```

**2. Start the MQTT broker**
```bash
docker run -d -p 1883:1883 --name mosquitto eclipse-mosquitto
```

**3. Run the backend** (in one terminal)
```bash
cd backend
python app.py
```

**4. Run the sensor simulator** (in a second terminal)
```bash
python sensors/simulator.py
```

**5. Check it's working**
- `http://localhost:5000/health` — pipeline status
- `http://localhost:5000/readings` — latest sensor readings (JSON)

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Reports whether the MQTT pipeline is connected and receiving data |
| `/readings` | GET | Returns the most recent sensor readings (`?limit=` to control how many, default 50, max 500) |

## License

MIT