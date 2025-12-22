#!/usr/bin/env python3
import os
import time
from datetime import datetime
from docker import DockerClient
from prometheus_client import start_http_server, Gauge, REGISTRY, GC_COLLECTOR, PLATFORM_COLLECTOR, PROCESS_COLLECTOR

# Disable default collectors to reduce overhead
REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
REGISTRY.unregister(PROCESS_COLLECTOR)


def main():
    # Connect to the Docker daemon via UNIX socket
    client = DockerClient(base_url="unix://var/run/docker.sock")

    # Define Prometheus metrics
    total_containers_gauge = Gauge(
        "docker_containers_total", "Total number of Docker containers"
    )
    running_containers_gauge = Gauge(
        "docker_containers_running_total", "Number of running Docker containers"
    )
    stopped_containers_gauge = Gauge(
        "docker_containers_stopped_total", "Number of stopped Docker containers"
    )
    others_containers_gauge = Gauge(
        "docker_containers_other_total",
        "Number of Docker containers in other states (not running or stopped)",
    )
    container_state_gauge = Gauge(
        "docker_container_state",
        "State of individual Docker containers (1=running, 0=stopped/other)",
        ["container_name", "container_id", "status"]
    )

    PORT = int(os.getenv("PORT", 9102))
    INTERVAL = int(os.getenv("INTERVAL", 60))  # Configurable interval
    start_http_server(PORT)
    print(f"Prometheus metrics available at http://localhost:{PORT}/metrics")

    previous_states = {}

    while True:
        try:
            # Use filters to reduce API response size - only get id, names, status
            all_containers = client.containers.list(all=True)
            total_count = len(all_containers)
            total_containers_gauge.set(total_count)

            running_count = 0
            stopped_count = 0
            others_count = 0
            current_states = {}

            for container in all_containers:
                container_name = container.attrs['Name'].lstrip('/')
                container_id = container.short_id
                status = container.status

                current_states[container_id] = (container_name, status)

                # Clear old metric only if status changed
                if container_id in previous_states:
                    old_name, old_status = previous_states[container_id]
                    if old_status != status:
                        try:
                            container_state_gauge.remove(old_name, container_id, old_status)
                        except KeyError:
                            pass

                state_value = 1 if status == "running" else 0
                container_state_gauge.labels(
                    container_name=container_name,
                    container_id=container_id,
                    status=status
                ).set(state_value)

                if status == "running":
                    running_count += 1
                elif status == "exited":
                    stopped_count += 1
                else:
                    others_count += 1

            # Remove metrics for deleted containers
            for old_id, (old_name, old_status) in previous_states.items():
                if old_id not in current_states:
                    try:
                        container_state_gauge.remove(old_name, old_id, old_status)
                    except KeyError:
                        pass

            previous_states = current_states

            running_containers_gauge.set(running_count)
            stopped_containers_gauge.set(stopped_count)
            others_containers_gauge.set(others_count)

            print(
                f"{datetime.now().astimezone().isoformat()} - Total: {total_count}, Running: {running_count}, Stopped: {stopped_count}, Others: {others_count}"
            )

            time.sleep(INTERVAL)
        except Exception as e:
            print(f"{datetime.now().isoformat()} - Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
