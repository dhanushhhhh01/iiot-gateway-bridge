# 🌐 IIoT Gateway Bridge

> Production-ready edge-to-cloud IIoT gateway. Connects industrial devices via OPC-UA, MQTT, and Modbus to cloud time-series databases. Features protocol normalization, anomaly detection, and multi-destination forwarding.
>
> [![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
> [![MQTT](https://img.shields.io/badge/MQTT-660066?style=for-the-badge&logo=mqtt&logoColor=white)](https://mqtt.org)
> [![OPC-UA](https://img.shields.io/badge/OPC--UA-0082C9?style=for-the-badge)](https://opcfoundation.org)
> [![InfluxDB](https://img.shields.io/badge/InfluxDB-22ADF6?style=for-the-badge&logo=influxdb&logoColor=white)](https://influxdata.com)
> [![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
>
> ---
>
> ## 🏗️ Architecture
>
> ```
> Industrial Devices
>     ├── OPC-UA Servers (PLCs, SCADA)
>     ├── MQTT Brokers (sensors, edge devices)
>     └── Modbus RTU/TCP (legacy equipment)
>            │
>            ▼
>     ┌─────────────────────────┐
>     │   Protocol Adapters     │  adapters/
>     │  opcua | mqtt | modbus  │
>     └──────────┬──────────────┘
>                │
>     ┌──────────▼──────────────┐
>     │   Normalization Layer   │  normalization/
>     │  schema | units | flags │
>     └──────────┬──────────────┘
>                │
>     ┌──────────▼──────────────┐
>     │      Forwarders         │  forwarders/
>     │  InfluxDB | Azure IoT   │
>     └─────────────────────────┘
> ```
>
> ---
>
> ## 📁 Project Structure
>
> ```
> iiot-gateway-bridge/
> ├── adapters/
> │   ├── opcua_adapter.py       # OPC-UA client with node subscription
> │   ├── mqtt_adapter.py        # MQTT subscriber with reconnect logic
> │   └── modbus_adapter.py      # Modbus TCP/RTU register polling
> ├── normalization/
> │   ├── schema.py              # NormalizedDataPoint dataclass
> │   ├── unit_converter.py      # Engineering unit conversion
> │   └── anomaly_flagger.py     # Threshold-based anomaly detection
> ├── forwarders/
> │   ├── influxdb_forwarder.py  # InfluxDB v2 line protocol writer
> │   └── azure_iot_forwarder.py # Azure IoT Hub device SDK forwarder
> ├── config/
> │   ├── devices.yaml           # Device/protocol configuration
> │   ├── mappings.yaml          # Tag/node ID mappings
> │   └── thresholds.yaml        # Anomaly detection thresholds
> ├── gateway.py                 # Main orchestrator
> ├── Dockerfile
> └── docker-compose.yml
> ```
>
> ---
>
> ## 🚀 Quick Start
>
> ```bash
> git clone https://github.com/dhanushhhhh01/iiot-gateway-bridge.git
> cd iiot-gateway-bridge
> cp .env.example .env
>
> # Edit config/devices.yaml with your device settings
> docker-compose up -d
> ```
>
> ### Sample Device Config (`config/devices.yaml`)
>
> ```yaml
> devices:
>   - id: motor_001
>     protocol: opcua
>     endpoint: opc.tcp://192.168.1.100:4840
>     poll_interval: 5
>     nodes:
>       - ns=2;i=2001  # Temperature
>       - ns=2;i=2002  # Vibration
>
>   - id: conveyor_sensors
>     protocol: mqtt
>     broker: mqtt://192.168.1.10:1883
>     topics:
>       - factory/conveyor/+/temperature
>       - factory/conveyor/+/speed
>
>   - id: legacy_plc
>     protocol: modbus
>     host: 192.168.1.200
>     port: 502
>     registers:
>       - { address: 100, type: holding, name: "pump_pressure" }
>       - { address: 101, type: holding, name: "flow_rate" }
>
> forwarders:
>   influxdb:
>     enabled: true
>     url: http://influxdb:8086
>     token: ${INFLUXDB_TOKEN}
>     org: factory
>     bucket: sensor_data
>   azure_iot:
>     enabled: false
>     connection_string: ${AZURE_IOT_CONNECTION_STRING}
> ```
>
> ---
>
> ## 📊 Data Flow
>
> Each data point is normalized to:
>
> ```python
> @dataclass
> class NormalizedDataPoint:
>     device_id: str
>     measurement: str
>     fields: Dict[str, float]
>     tags: Dict[str, str]
>     timestamp: datetime
>     unit: str = ""
>     quality: str = "GOOD"  # GOOD | BAD | UNCERTAIN
> ```
>
> ---
>
> ## 📬 Author
>
> **Dhanush Ramesh Babu** | [LinkedIn](https://linkedin.com/in/dhanushrameshbabu16) | MSc. Industry 4.0 @ SRH Berlin | 🟢 Open to Werkstudent/Internship
