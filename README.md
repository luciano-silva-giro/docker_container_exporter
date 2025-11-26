
# docker_container_exporter

A Prometheus exporter that collects metrics about Docker containers. The exporter is written in Python and uses the Docker SDK to interact with the Docker API.

The exporter exposes the following metrics:

- `docker_containers_total`: Total number of Docker containers
- `docker_containers_running_total`: Number of running Docker containers
- `docker_containers_stopped_total`: Number of stopped Docker containers
- `docker_containers_other_total`: Number of Docker containers in other states (not running or stopped)
- `docker_container_state`: State of individual Docker containers with labels (1=running, 0=stopped/other)
  - Labels: `container_name`, `container_id`, `status`

The `docker_container_state` metric allows you to track individual containers and create alerts in Prometheus/Alertmanager for specific containers that start or stop.

## Table of contents

- [Quick Installation](#quick-installation)
- [Requirements](#requirements)
- [Development](#development)
- [Running the Application](#running-the-application)
  - [Using Python](#using-python)
  - [Using Docker](#using-docker)
  - [As a Linux Service](#as-a-linux-service)
- [Configuration](#configuration)
- [Alerting Examples](#alerting-examples)

## Quick Installation

Install the exporter as a systemd service on any Linux machine with a single command:

```sh
curl -fsSL https://raw.githubusercontent.com/oriolrius/docker_container_exporter/main/install.sh | sudo bash
```

This will:
- Install Python and dependencies
- Clone the repository to `/opt/docker_container_exporter`
- Set up a virtual environment
- Create and start a systemd service
- Expose metrics on port 9000 (configurable)

To use a custom port:

```sh
curl -fsSL https://raw.githubusercontent.com/oriolrius/docker_container_exporter/main/install.sh | sudo PORT=8080 bash
```

After installation, metrics will be available at `http://localhost:9000/metrics`

## Requirements

- Docker
- Python 3.10+
- Prometheus (for scraping metrics)

## Development

1. **Clone the repository:**

    ```sh
    git clone git@github.com:oriolrius/docker_container_exporter.git
    cd docker_container_exporter
    ```

1. **Create and activate a virtual environment:**

    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

1. **Install the dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

1. **Configure the default port:**

    ```sh
    export PORT=9000
    ```

## Running the Application

### Using Python

1. **Run the application:**

    ```sh
    python containers_running.py
    ```

2. **Access the Prometheus metrics:**

    Open your browser and go to `http://localhost:9000/metrics`.

### Using Docker

1. Get files `docker-compose.yml` and `.env` from the repository.

    ```sh
    wget https://raw.githubusercontent.com/oriolrius/docker_container_exporter/main/docker-compose.yml
    wget https://raw.githubusercontent.com/oriolrius/docker_container_exporter/main/.env
    ```

1. Edit them to set the desired configuration.

    ```sh
    nano .env
    nano docker-compose.yml
    ```

1. **Run the stack:**

    ```sh
    docker-compose up
    ```

1. **Access the Prometheus metrics:**

    Open your browser and go to `http://localhost:9000/metrics`.

### As a Linux Service

To run the exporter as a systemd service:

1. **Copy the service file:**

    ```sh
    sudo cp docker-container-exporter.service /etc/systemd/system/
    ```

2. **Edit the service file to set your paths and user:**

    ```sh
    sudo nano /etc/systemd/system/docker-container-exporter.service
    ```

    Update `User`, `WorkingDirectory`, and `ExecStart` paths.

3. **Enable and start the service:**

    ```sh
    sudo systemctl daemon-reload
    sudo systemctl enable docker-container-exporter
    sudo systemctl start docker-container-exporter
    ```

4. **Check status:**

    ```sh
    sudo systemctl status docker-container-exporter
    sudo journalctl -u docker-container-exporter -f
    ```

## Configuration

The exporter uses the `PORT` environment variable to configure the HTTP server port (default: 9000).

## Alerting Examples

With the `docker_container_state` metric, you can create alerts in Prometheus/Alertmanager for specific containers:

### Alert when any container stops

```yaml
groups:
  - name: docker_containers
    rules:
      - alert: ContainerStopped
        expr: docker_container_state{status="exited"} == 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.container_name }} has stopped"
          description: "Container {{ $labels.container_name }} (ID: {{ $labels.container_id }}) is no longer running"
```

### Alert when a specific container stops

```yaml
      - alert: CriticalContainerStopped
        expr: docker_container_state{container_name="my-important-app", status="exited"} == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Critical container my-important-app has stopped"
```

### Alert when a container starts

```yaml
      - alert: ContainerStarted
        expr: docker_container_state{status="running"} == 1
        for: 1m
        labels:
          severity: info
        annotations:
          summary: "Container {{ $labels.container_name }} is now running"
```

## Grafana Alloy

Using Grafana Alloy you can collect the metrics from the exporter and send a Promtheus compatiable server, for instance Grafana Mimir.

Of course, you can use Prometheus directly and any other Prometheus compatible agent.

Next you can see an example of the configuration for Alloy to collect the metrics from the exporter and send them to Grafana Mimir (metrics database compatible with Prometheus).

```config.alloy
prometheus.scrape "node_containers" {
  targets    = [
    { "__address__" = "localhost:9000",
      "__scheme__" = "http",
      "instance" = "iiot",
      "job" = "node_containers",
      "__scrape_interval__" = "10s",
     },
  ]
  forward_to = [prometheus.remote_write.mimir.receiver]
}

prometheus.remote_write "mimir" {
  url = "http://YOUR_SERVER/api/v1/push"
}

```

## Author

Oriol Rius

- email: <oriol@joor.net>

- https://oriolrius.me - Professional services

- https://oriolrius.cat - Personal blog since, July 2000

## License

This project is licensed under the MIT License.
