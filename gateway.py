"""
IIoT Gateway Bridge - Main orchestrator.

Connects industrial protocols (OPC-UA, MQTT, Modbus) to cloud/time-series databases.
Architecture: Protocol Adapters -> Normalization -> Forwarders
"""
import asyncio
import logging
import signal
import yaml
from pathlib import Path
from typing import Dict, List

from adapters.opcua_adapter import OPCUAAdapter
from adapters.mqtt_adapter import MQTTAdapter
from adapters.modbus_adapter import ModbusAdapter
from normalization.schema import NormalizedDataPoint
from normalization.anomaly_flagger import AnomalyFlagger
from forwarders.influxdb_forwarder import InfluxDBForwarder
from forwarders.azure_iot_forwarder import AzureIoTForwarder

logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("IIoTGateway")


class IIoTGateway:
      """
          Main gateway orchestrator.

                  Manages lifecycle of all protocol adapters and data forwarders.
                      Handles reconnection, error recovery, and graceful shutdown.
                          """

    def __init__(self, config_path: str = "config/devices.yaml"):
              self.config = self._load_config(config_path)
              self.adapters = {}
              self.forwarders = {}
              self.anomaly_flagger = AnomalyFlagger(
                  config_path="config/thresholds.yaml"
              )
              self._running = False
              self._data_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)

    def _load_config(self, path: str) -> Dict:
              with open(path) as f:
                            return yaml.safe_load(f)

          async def initialize(self):
                    """Initialize all configured adapters and forwarders."""
                    logger.info("Initializing IIoT Gateway Bridge...")

        # Initialize adapters
        for device in self.config.get("devices", []):
                      protocol = device.get("protocol", "").lower()

            if protocol == "opcua":
                              adapter = OPCUAAdapter(
                                                    endpoint=device["endpoint"],
                                                    node_ids=device.get("nodes", []),
                                                    polling_interval=device.get("poll_interval", 5)
                              )
                              self.adapters[device["id"]] = adapter

elif protocol == "mqtt":
                  adapter = MQTTAdapter(
                                        broker=device["broker"],
                                        topics=device.get("topics", []),
                                        device_id=device["id"]
                  )
                  self.adapters[device["id"]] = adapter

elif protocol == "modbus":
                  adapter = ModbusAdapter(
                                        host=device["host"],
                                        port=device.get("port", 502),
                                        registers=device.get("registers", []),
                                        device_id=device["id"]
                  )
                  self.adapters[device["id"]] = adapter

        logger.info(f"Initialized {len(self.adapters)} device adapters")

        # Initialize forwarders
        forwarder_config = self.config.get("forwarders", {})

        if forwarder_config.get("influxdb", {}).get("enabled", False):
                      self.forwarders["influxdb"] = InfluxDBForwarder(
                                        **forwarder_config["influxdb"]
                      )

        if forwarder_config.get("azure_iot", {}).get("enabled", False):
                      self.forwarders["azure_iot"] = AzureIoTForwarder(
                                        **forwarder_config["azure_iot"]
                      )

        logger.info(f"Initialized {len(self.forwarders)} forwarders")

    async def run(self):
              """Main gateway run loop."""
              self._running = True
              logger.info("Gateway running. Press Ctrl+C to stop.")

        # Start all adapters
              adapter_tasks = [
                            asyncio.create_task(
                                              adapter.start(self._data_queue),
                                              name=f"adapter-{device_id}"
                            )
                            for device_id, adapter in self.adapters.items()
              ]

        # Start data processor
        processor_task = asyncio.create_task(
                      self._process_data(),
                      name="data-processor"
        )

        try:
                      await asyncio.gather(processor_task, *adapter_tasks)
except asyncio.CancelledError:
              logger.info("Gateway shutdown initiated...")
finally:
              await self.shutdown()

    async def _process_data(self):
              """Process data from queue: normalize, flag anomalies, forward."""
              while self._running:
                            try:
                                              raw_data = await asyncio.wait_for(
                                                                    self._data_queue.get(), timeout=1.0
                                              )

                                # Normalize the data point
                                              point = NormalizedDataPoint.from_raw(raw_data)

                                # Check for anomalies
                                              anomalies = self.anomaly_flagger.check(point)
                                              if anomalies:
                                                                    logger.warning(f"Anomaly detected: {anomalies} on {point.device_id}")
                                                                    point.tags["anomaly"] = "true"

                                              # Forward to all configured destinations
                                              for name, forwarder in self.forwarders.items():
                                                                    try:
                                                                                              await forwarder.forward(point)
                            except Exception as e:
                                                      logger.error(f"Forwarder {name} error: {e}")

                            except asyncio.TimeoutError:
                                              continue
except Exception as e:
                logger.error(f"Data processing error: {e}")

    async def shutdown(self):
              """Gracefully shutdown all adapters and forwarders."""
              logger.info("Shutting down gateway...")
              self._running = False

        for device_id, adapter in self.adapters.items():
                      try:
                                        await adapter.stop()
except Exception as e:
                logger.error(f"Error stopping adapter {device_id}: {e}")

        for name, forwarder in self.forwarders.items():
                      try:
                                        await forwarder.close()
except Exception as e:
                logger.error(f"Error closing forwarder {name}: {e}")

        logger.info("Gateway shutdown complete")


async def main():
      gateway = IIoTGateway(config_path="config/devices.yaml")
      await gateway.initialize()

    # Handle graceful shutdown
      loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
              loop.add_signal_handler(sig, lambda: asyncio.create_task(gateway.shutdown()))

    await gateway.run()


if __name__ == "__main__":
      asyncio.run(main())
