#!/usr/bin/env python3
import os
import time
from datetime import datetime
from docker import DockerClient
from prometheus_client import start_http_server, Gauge


def main():
    """
    Connects to the Docker daemon via UNIX socket and collects Prometheus metrics for Docker containers.

    This function starts a Prometheus HTTP server on a specified port and continuously updates metrics for the following:
    - Total number of Docker containers
    - Number of running Docker containers
    - Number of stopped Docker containers
    - Number of Docker containers in other states (not running or stopped)
    - Individual container state with labels (name, status, id)

    The function retrieves all containers, counts them based on their status, and updates the Prometheus gauges accordingly.
    It also logs the container counts with a timestamp in ISO format.

    If an error occurs while retrieving or updating metrics, the function logs the error with a timestamp in ISO format.

    The function waits for 10 seconds before updating metrics again, and 5 seconds after an error occurs.

    Note: Make sure to have the Docker daemon running and the Prometheus HTTP server accessible on the specified port.

    Raises:
      Exception: If an error occurs while retrieving or updating metrics.

    """
    # Connect to the Docker daemon via UNIX socket
    client = DockerClient(base_url="unix://var/run/docker.sock")

    # Define Prometheus metrics to collect
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

    # Individual container state metric with labels
    container_state_gauge = Gauge(
        "docker_container_state",
        "State of individual Docker containers (1=running, 0=stopped/other)",
        ["container_name", "container_id", "status"]
    )

    # Start the Prometheus HTTP server on the specified port
    PORT = int(os.getenv("PORT", 9000))
    start_http_server(PORT)
    print(f"Prometheus metrics available at http://localhost:{PORT}/metrics")

    while True:
        try:
            # Get all containers
            all_containers = client.containers.list(all=True)
            total_count = len(all_containers)
            total_containers_gauge.set(total_count)

            # Initialize counts
            running_count = 0
            stopped_count = 0
            others_count = 0

            # Track current containers to clean up stale metrics
            current_containers = set()

            # Count containers based on their status and update individual metrics
            for container in all_containers:
                container_name = container.name
                container_id = container.short_id
                status = container.status
                
                # Track this container
                current_containers.add(container_id)
                
                # Set state value: 1 for running, 0 for stopped/other
                state_value = 1 if status == "running" else 0
                
                # Update individual container metric
                container_state_gauge.labels(
                    container_name=container_name,
                    container_id=container_id,
                    status=status
                ).set(state_value)
                
                # Count by status
                if status == "running":
                    running_count += 1
                elif status == "exited":
                    stopped_count += 1
                else:
                    others_count += 1

            # Update Prometheus gauges
            running_containers_gauge.set(running_count)
            stopped_containers_gauge.set(stopped_count)
            others_containers_gauge.set(others_count)

            # Log the counts with timestamp in ISO format (Line 49)
            current_time = datetime.now().astimezone().isoformat()
            print(
                f"{current_time} - Total: {total_count}, Running: {running_count}, Stopped: {stopped_count}, Others: {others_count}"
            )

            # Wait before updating metrics again
            time.sleep(60)
        except Exception as e:
            # Log the error with timestamp in ISO format (Line 54)
            current_time = datetime.now().isoformat()
            print(f"{current_time} - An error occurred: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
