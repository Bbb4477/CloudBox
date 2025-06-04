import socket
import subprocess
import json
import os
from time import sleep
import yaml
import re
import base64
import struct

HOST = '0.0.0.0'
SHAREHOST = '192.168.32.133'
PORT = 5000


def load_port_assignments():
    """Load port assignments from port_assigned.json."""
    try:
        if os.path.exists("port_assigned.json"):
            with open("port_assigned.json", "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"[Agent] Error loading port_assigned.json: {e}")
        return {}


def save_port_assignments(assignments):
    """Save port assignments to port_assigned.json."""
    try:
        with open("port_assigned.json", "w") as f:
            json.dump(assignments, f, indent=2)
    except Exception as e:
        print(f"[Agent] Error saving port_assigned.json: {e}")

def get_compose_services(box_dir: str) -> list:
    """Parse docker-compose.yml to get service names."""
    docker_compose_path = os.path.join(box_dir, "docker-compose.yml")
    try:
        with open(docker_compose_path, "r") as f:
            compose_data = yaml.safe_load(f)
        services = list(compose_data.get('services', {}).keys())
        return services if services else []
    except Exception as e:
        print(f"[Agent] Error parsing docker-compose.yml in {box_dir}: {e}")
        return []

def availablePort(box_dir):
    """Return a list of available ports, checking port_assigned.json and netstat."""
    try:
        # Load allowed ports from agentConfig.json
        with open("agentConfig.json", "r") as f:
            config = json.load(f)
        allowed_ports = config.get("ports", [])

        # Load assigned ports from port_assigned.json
        assigned_ports = load_port_assignments()
        used_ports = set()
        for box, services in assigned_ports.items():
            if isinstance(services, dict):  # Ensure services is a dictionary
                for service, port in services.items():
                    if isinstance(port, int):  # Ensure port is an integer
                        used_ports.add(port)

        # Check ports in use by netstat
        port_pattern = '|'.join(str(port) for port in allowed_ports)
        cmd = f"netstat -tuln | grep -E ':({port_pattern})' | awk '{{print $4}}' | cut -d':' -f2"
        result = run_command(cmd)

        if result.startswith("[ERROR]") or result.startswith("[EXCEPTION]"):
            used_ports_from_netstat = set()
        else:
            used_ports_from_netstat = {int(port) for port in result.split('\n') if port.isdigit()}
        used_ports.update(used_ports_from_netstat)

        # Filter allowed ports to exclude used ones
        available_ports = [port for port in allowed_ports if port not in used_ports]
        return available_ports
    except Exception as e:
        print(f"[Agent] Error in availablePort: {e}")
        return []

def startBox(arg: str) -> bytes:
    """Start a box, assign ports to services, and update port_assigned.json."""
    box_dir = os.path.join(os.getcwd(), "Box", arg)
    box_name = box_dir.split("/")[-1]
    if not os.path.isdir(box_dir):
        return f"[Agent] Directory {box_dir} does not exist.".encode()

    # Get service names from docker-compose.yml
    services = get_compose_services(box_dir)
    if not services:
        return f"[Agent] No valid services found in docker-compose.yml.".encode()

    # Get available ports
    available_ports = availablePort(box_dir)
    if len(available_ports) < len(services):
        return f"[Agent] Not enough available ports for services.".encode()

    # Load port assignments
    assignments = load_port_assignments()
    if box_name not in assignments:
        assignments[box_name] = {}

    # Parse docker-compose.yml to check for PORT placeholders
    docker_compose_path = os.path.join(box_dir, "docker-compose.yml")
    try:
        with open(docker_compose_path, "r") as f:
            compose_data = yaml.safe_load(f)
        content = f.read()
        f.seek(0)  # Reset file pointer after reading
    except Exception as e:
        return f"[Agent] Error reading docker-compose.yml: {e}".encode()

    # Assign ports to services with PORT placeholders
    port_index = 0
    for service_name in services:
        service_config = compose_data.get('services', {}).get(service_name, {})
        ports = service_config.get('ports', [])
        for port in ports:
            if isinstance(port, str) and 'PORT' in port:
                if port_index >= len(available_ports):
                    return f"[Agent] Not enough available ports for service {service_name}.".encode()
                assigned_port = available_ports[port_index]
                content = re.sub(r'"PORT(?::\d+)?":', f'"{assigned_port}":', content)
                assignments[box_name][service_name] = assigned_port
                port_index += 1
            elif isinstance(port, str) and ':' in port:
                external_port = port.split(':')[0]
                if external_port.isdigit():
                    assignments[box_name][service_name] = int(external_port)
            elif isinstance(port, dict) and 'published' in port:
                external_port = port.get('published')
                if external_port and str(external_port).isdigit():
                    assignments[box_name][service_name] = int(external_port)

    # Write updated docker-compose.yml
    try:
        with open(docker_compose_path, "w") as f:
            f.write(content)
    except Exception as e:
        return f"[Agent] Error updating docker-compose.yml: {e}".encode()

    # Save updated port assignments
    save_port_assignments(assignments)

    # Start the box
    try:
        run_command(f"tmux new-session -d -s {box_dir} -x 100 -y 1000")
        run_command(f"tmux send-keys -t {box_dir} 'cd {box_dir};docker-compose up' C-m")
        sleep(2)
        output = run_command(f"tmux capture-pane -t {box_dir} -p")
        return f"[Agent] Box started at {SHAREHOST} with ports {assignments[box_name]}\n{output}".encode()
    except subprocess.CalledProcessError as e:
        return f"[Agent] Error starting docker-compose:\n{e.output}".encode()


def stopBox(arg: str) -> bytes:
    """Stop a box and release its ports from port_assigned.json."""
    box_dir = os.path.join(os.getcwd(), "Box", arg)
    box_name = box_dir.split("/")[-1]

    if not os.path.isdir(box_dir):
        print("Box not exist")
        return f"[Agent] Directory {box_dir} does not exist.".encode()

    try:
        run_command(f"tmux send-keys -t {box_dir} C-c ")
        sleep(2)
        run_command(f"tmux kill-session -t {box_dir}")

        # Remove ports from port_assigned.json
        assignments = load_port_assignments()
        if box_name in assignments:
            del assignments[box_name]
            save_port_assignments(assignments)

        return f"[Agent] Box {box_name} stopped successfully".encode()
    except Exception as e:
        return f"[Agent] Error stopping box: {e}".encode()


def start_agent_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[Agent] Listening on port {PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                print(f"[Agent] Connection from {addr}")
                data = conn.recv(1024).decode().strip()
                if data.startswith(SECRET_PATH):
                    command = data[len(SECRET_PATH):].strip()
                    print(f"[Agent] Valid command received")
                    try:
                        output = subprocess.check_output(command, shell=True, text=True)
                        conn.sendall(output.encode())
                    except Exception as e:
                        conn.sendall(str(e).encode())
                elif data.__contains__("SpecialExecution"):
                    if data[16:].split(" ")[0] == SECRET_PATH:
                        command = data[len("SpecialExecution" + SECRET_PATH):].strip()
                        cmm = command.split(" ")
                        if cmm[0] == "box_start":
                            if len(cmm) < 2:
                                print(f"[Agent] Invalid command format received")
                                conn.sendall(b"Invalid Command format.")
                            else:
                                print(f"[Agent] Valid command received: Box Start {cmm[1]}")
                                conn.sendall(startBox(cmm[1]))
                        elif cmm[0] == "box_stop":
                            if len(cmm) < 2:
                                print(f"[Agent] Invalid command format received")
                                conn.sendall(b"Invalid Command format.")
                            else:
                                print(f"[Agent] Valid command received: Box Stop {cmm[1]}")
                                try:
                                    conn.sendall(stopBox(cmm[1]))
                                except Exception as e:
                                    conn.sendall(str(e).encode())
                        elif cmm[0] == "box_status":
                            try:
                                conn.sendall(boxList())
                            except Exception as e:
                                conn.sendall(str(e).encode())
                        elif cmm[0] == "box_inspect":
                            if len(cmm) < 2:
                                print(f"[Agent] Invalid command format received")
                                conn.sendall(b"Invalid Command format.")
                            else:
                                print(f"[Agent] Valid command received: Box Inspect {cmm[1]}")
                                try:
                                    conn.sendall(inspectBox(cmm[1]))
                                except Exception as e:
                                    conn.sendall(str(e).encode())
                        else:
                            print(f"[Agent] Invalid command format received")
                            conn.sendall(b"Invalid Command format.")
                    else:
                        conn.sendall(b"Invalid API key/path.")
                else:
                    print("[Agent] Invalid API key/path. Ignored.")
                    conn.sendall(b"Invalid API key/path.")

def start_agent_listener_InjectionFix():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"[Agent] Listening on port {PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(1024).decode()
                secret = data.split(' ')[0]
                cmm = data.split(' ')
                print(cmm)
                if secret != SECRET_PATH:
                    conn.sendall("Invalid secret!".encode())
                    continue


                if cmm[1] == "box_status":
                    try:
                        conn.sendall(boxList())
                        print(f"[Agent] Valid command received: Box List")
                    except Exception as e:
                        conn.sendall(str(e).encode())


                elif cmm[1] == "box_start":
                    if len(cmm) < 3:
                        print(f"[Agent] Invalid command format received")
                        conn.sendall(b"Invalid Command format.")
                    else:
                        print(f"[Agent] Valid command received: Box start {cmm[2]}")
                        try:
                            conn.sendall(startBox(cmm[2]))
                        except Exception as e:
                            conn.sendall(str(e).encode())


                elif cmm[1] == "box_stop":
                    if len(cmm) < 3:
                        print(f"[Agent] Invalid command format received")
                        conn.sendall(b"Invalid Command format.")
                    else:
                        print(f"[Agent] Valid command received: Box Stop {cmm[2]}")
                        try:
                            conn.sendall(stopBox(cmm[2]))
                        except Exception as e:
                            conn.sendall(str(e).encode())


                elif cmm[1] == "box_inspect":
                    if len(cmm) < 3:
                        print(f"[Agent] Invalid command format received")
                        conn.sendall(b"Invalid Command format.")
                    else:
                        print(f"[Agent] Valid command received: Box Inspect {cmm[2]}")
                        try:
                            conn.sendall(inspectBox(cmm[2]))
                        except Exception as e:
                            conn.sendall(str(e).encode())
                else:
                    try:
                        secret, length_str, rest = data.split(' ', 2)
                        length = int(length_str)
                        if secret != SECRET_PATH:
                            conn.sendall("Invalid secret!".encode())
                            continue
                        while len(rest) < length:
                            rest += conn.recv(1024).decode()
                        b64_command = rest[:length]
                        json_str = base64.b64decode(b64_command).decode()
                        commands = json.loads(json_str)
                        ans = createNewBoxAgent(commands)
                        print(ans)
                        conn.sendall(ans.encode())
                    except Exception as e:
                        print(e)

def createNewBoxAgent(arg):
    boxID = arg["boxID"]
    compose = arg["compose"]
    try:
        run_command(f"cd Box; mkdir {boxID}")
        run_command(f"cd Box; cd {boxID}; echo \"{compose}\" > docker-compose.yml;")
    except Exception as e:
        return f"[EXCEPTION] {str(e)}"
    return f"Create box {boxID} Successfully"

def list_available_services():
    DOCKER_REFERENCE_PATH = os.path.join(os.getcwd(), "Box")
    services = [
        name for name in os.listdir(DOCKER_REFERENCE_PATH)
        if os.path.isdir(os.path.join(DOCKER_REFERENCE_PATH, name))
    ]
    return services

def boxList() -> bytes:
    DOCKER_REFERENCE_PATH = run_command("pwd") + "/Box"
    services = [
        name for name in os.listdir(DOCKER_REFERENCE_PATH)
        if os.path.isdir(os.path.join(DOCKER_REFERENCE_PATH, name))
    ]
    joined = ' '.join(services)
    b = joined.encode()
    return b

def inspectBox(arg: str) -> bytes:
    return b"Inspect not implemented"

def extract_service_keys(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
        services = data.get('services', {})
        return list(services.keys())

def run_command(cmd: str) -> str:
    try:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"[ERROR] {result.stderr.strip()}"
    except Exception as e:
        return f"[EXCEPTION] {str(e)}"


def checkBoxStatus(box_id: str) -> str:
    """Check the status of a box by verifying if all services in docker-compose.yml are running in docker ps."""
    box_dir = os.path.join(os.getcwd(), "Box", box_id)
    box_name = box_dir.split("/")[-1]

    # Check if box directory exists
    if not os.path.isdir(box_dir):
        return "nonExisted"

    # Get services from docker-compose.yml
    services = get_compose_services(box_dir)
    if not services:
        return "noServices"

    # Get running containers from docker ps
    dock_output = run_command("docker ps --format '{{.Names}}'")
    if dock_output.startswith("[ERROR]") or dock_output.startswith("[EXCEPTION]"):
        print(f"[Agent] Error running docker ps: {dock_output}")
        return "errorDockerPs"

    # Check if all services are running
    running_containers = set(dock_output.splitlines())
    expected_containers = {f"{box_name.lower()}_{service}_1" for service in services}

    if expected_containers.issubset(running_containers):
        return "running"
    return "partial" if any(cont in running_containers for cont in expected_containers) else "stopped"


def overviewAgent() -> bytes:
    """Generate an overview of the agent's boxes, their status, and resource usage."""
    # Define tmux session name for docker stats
    stats_session = "agent_stats"

    # Check if tmux session exists, start if not
    tmux_check = run_command(f"tmux has-session -t {stats_session}")
    if tmux_check.startswith("[ERROR]") or tmux_check.startswith("[EXCEPTION]"):
        run_command(f"tmux new-session -d -s {stats_session} -x 100 -y 1000")
        run_command(f"tmux send-keys -t {stats_session} 'docker stats --no-stream --format json' C-m")
        sleep(1)  # Wait for stats to initialize

    # Capture tmux output
    stats_output = run_command(f"tmux capture-pane -t {stats_session} -p")
    if stats_output.startswith("[ERROR]") or stats_output.startswith("[EXCEPTION]"):
        return json.dumps({
            "error": f"Failed to capture stats: {stats_output}"
        }).encode()

    # Parse docker stats JSON output
    container_stats = {}
    for line in stats_output.splitlines():
        try:
            stats = json.loads(line.strip())
            container_stats[stats["Name"]] = {
                "cpu": stats["CPUPerc"],
                "memory": stats["MemUsage"].split('/')[0].strip()
            }
        except json.JSONDecodeError:
            continue

    # Load port assignments
    assignments = load_port_assignments()

    # Get agent details
    agent_info = {
        "ip": SHAREHOST,
        "port": str(PORT),
        "name": run_command("hostname").strip(),
        "status": "running",
        "box": {}
    }

    # Iterate through boxes in the Box directory
    box_dir = os.path.join(os.getcwd(), "Box")
    if not os.path.isdir(box_dir):
        return json.dumps({"agent01": agent_info}).encode()

    for box_name in os.listdir(box_dir):
        box_path = os.path.join(box_dir, box_name)
        if not os.path.isdir(box_path):
            continue

        # Parse docker-compose.yml for services
        docker_compose_path = os.path.join(box_path, "docker-compose.yml")
        try:
            with open(docker_compose_path, "r") as f:
                compose_data = yaml.safe_load(f)
            services = compose_data.get('services', {})
        except Exception as e:
            print(f"[Agent] Error parsing docker-compose.yml in {box_path}: {e}")
            continue

        # Check box status using docker ps
        dock_output = run_command("docker ps --format '{{.Names}}'")
        running_containers = set(dock_output.splitlines()) if not dock_output.startswith("[ERROR]") else set()

        box_status = "stopped"
        box_info = {}
        for service_name in services:
            container_name = f"{box_name}_{service_name}_1"  # Standard Docker Compose naming
            if container_name in running_containers:
                box_status = "running"
                # Get port from port_assigned.json
                port = assignments.get(box_name, {}).get(service_name, "unknown")
                box_info[service_name] = {
                    "status": "running",
                    "url": f"{SHAREHOST}:{port}" if port != "unknown" else "unknown",
                    "cpu": container_stats.get(container_name, {}).get("cpu", "0%"),
                    "memory": container_stats.get(container_name, {}).get("memory", "0B")
                }
            else:
                box_info[service_name] = {
                    "status": "stopped",
                    "url": "none",
                    "cpu": "0%",
                    "memory": "0B"
                }

        agent_info["box"][box_name] = box_info

    # Wrap in agent01 key as per requested format
    result = {"agent01": agent_info}
    return json.dumps(result, indent=2).encode()


def stopAgentStats() -> bytes:
    """Stop the agent_stats tmux session."""
    stats_session = "agent_stats"
    try:
        run_command(f"tmux send-keys -t {stats_session} C-c")
        sleep(1)
        run_command(f"tmux kill-session -t {stats_session}")
        return f"[Agent] Stats session stopped successfully".encode()
    except Exception as e:
        return f"[Agent] Error stopping stats session: {e}".encode()

if __name__ == "__main__":
    f = open("agentConfig.json", "r")
    o = json.load(f)
    SECRET_PATH = o['API']
    ASSIGNABLE_PORTS = o['ports']
    # while(True):
    #     print(overviewAgent().decode("utf-8"))
    #     sleep(2)
    # start_agent_listener_InjectionFix()
    print(startBox("1749043882_gZYeu7UNef_wordpress"))