# agent_listener_with_api_key.py
import socket
import subprocess
import json
import os
from time import sleep
import yaml
import re
import base64
import struct
import logging
import fcntl

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

HOST = '0.0.0.0'
SHAREHOST = '192.168.32.133'
PORT = 5000


def load_port_allocations(write=False):
    """Load or save the port_allocations.json file with thread-safe access."""
    port_file = os.path.join(os.getcwd(), "Box", "port_allocations.json")
    lock_file = port_file + ".lock"

    # Ensure port_allocations.json exists
    if not os.path.exists(port_file) and write:
        with open(port_file, "w") as f:
            json.dump({}, f)

    # Use file lock for thread safety
    with open(lock_file, "w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            if write:
                with open(port_file, "r") as f:
                    allocations = json.load(f) if os.path.getsize(port_file) > 0 else {}
                return allocations, port_file
            else:
                with open(port_file, "r") as f:
                    return json.load(f) if os.path.getsize(port_file) > 0 else {}
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

def save_port_allocations(allocations, port_file):
    """Save the port_allocations to the port_file with thread-safe access."""
    lock_file = port_file + ".lock"
    with open(lock_file, "w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            with open(port_file, "w") as f:
                json.dump(allocations, f, indent=2)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

def availablePort() -> list:
    """Return a list of available ports from agentConfig.json, excluding assigned ports and system-used ports."""
    try:
        # Load allowed ports from agentConfig.json
        with open("agentConfig.json", "r") as f:
            config = json.load(f)
        allowed_ports = config["ports"]  # e.g., [10000, 10001, 10002, 10003]

        # Load current port allocations
        allocations = load_port_allocations()

        # Collect all assigned ports from port_allocations.json
        used_ports = set()
        for box_id, ports in allocations.items():
            for service, port in ports.get("port", {}).items():
                if port != "expose" and port.isdigit():
                    used_ports.add(int(port))

        # Check system-used ports with netstat
        cmd = "netstat -tuln | awk '{print $4}' | grep -E ':[0-9]+' | cut -d':' -f2"
        result = run_command(cmd)
        if result.startswith("[ERROR]") or result.startswith("[EXCEPTION]"):
            logging.error(f"[Agent] netstat failed: {result}")
            # Fallback to only checking allocations if netstat fails
            system_ports = set()
        else:
            system_ports = {int(port) for port in result.split('\n') if port.isdigit()}

        # Return ports that are allowed, not assigned, and not used by the system
        available_ports = [port for port in allowed_ports if port not in used_ports and port not in system_ports]
        if not available_ports:
            logging.error("[Agent] No available ports found after checking allocations and system")
        return available_ports
    except Exception as e:
        logging.error(f"[Agent] Error finding available ports: {str(e)}")
        return []

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

                elif cmm[1] == "box_delete":  # New command
                    if len(cmm) < 3:
                        print(f"[Agent] Invalid command format received")
                        conn.sendall(b"Invalid Command format.")
                    else:
                        print(f"[Agent] Valid command received: Box Delete {cmm[2]}")
                        try:
                            conn.sendall(deleteBox(cmm[2]))
                        except Exception as e:
                            conn.sendall(str(e).encode())

                elif cmm[1] == "check_box":
                    if len(cmm) < 3:
                        print(f"[Agent] Invalid command format received")
                        conn.sendall(b"Invalid Command format.")
                    else:
                        print(f"[Agent] Valid command received: Box Start {cmm[2]}")
                        try:
                            conn.sendall(checkBoxStatus(cmm[2]).encode())
                        except Exception as e:
                            conn.sendall(str(e).encode())

                elif cmm[1] == "agent_stats":
                    print(f"[Agent] Valid command received: Box Overview")
                    try:
                        conn.sendall(overviewAgent())
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
    install_guide = arg.get("installGuide", "")  # Get installGuide from payload, default to empty string
    try:
        run_command(f"cd Box; mkdir {boxID}")
        run_command(f"cd Box; cd {boxID}; echo \"{compose}\" > docker-compose.yml;")
        if install_guide:
            # Write installGuide.txt if it exists in the payload
            run_command(f"cd Box; cd {boxID}; echo \"{install_guide}\" > installGuide.txt;")
    except Exception as e:
        return f"[EXCEPTION] {str(e)}"
    return f"Create box {boxID} Successfully"

def render_install_guide(box_dir: str, share_host: str, port: str) -> str:
    """Render installGuide.txt with database credentials and port information."""
    try:
        # Read installGuide.txt
        guide_path = os.path.join(box_dir, "installGuide.txt")
        if not os.path.exists(guide_path):
            logging.warning(f"[Agent] installGuide.txt not found in {box_dir}")
            return ""

        with open(guide_path, "r") as f:
            guide_content = f.read()

        # Read docker-compose.yml to extract database credentials
        compose_path = os.path.join(box_dir, "docker-compose.yml")
        with open(compose_path, "r") as f:
            compose_content = f.read()

        # Extract DB_name, DB_username, DB_password using regex
        db_name = re.search(r"MYSQL_DATABASE:\s*(\w+)", compose_content)
        db_username = re.search(r"MYSQL_USER:\s*(\w+)", compose_content)
        db_password = re.search(r"MYSQL_PASSWORD:\s*(\S+)", compose_content)

        if not (db_name and db_username and db_password):
            logging.error(f"[Agent] Failed to extract database credentials from {compose_path}")
            return ""

        db_name = db_name.group(1)
        db_username = db_username.group(1)
        db_password = db_password.group(1)

        # Replace placeholders in installGuide.txt
        rendered_guide = guide_content.replace("<DB_name>", db_name)
        rendered_guide = rendered_guide.replace("<DB_username>", db_username)
        rendered_guide = rendered_guide.replace("<DB_password>", db_password)
        rendered_guide = rendered_guide.replace("<host>", share_host)
        rendered_guide = rendered_guide.replace("<port>", port)
        # Replace tutorial link placeholder (you can set a default or make it configurable)
        rendered_guide = rendered_guide.replace("<link_to_tutorial>", "https://www.drupal.org/docs/installation")

        return rendered_guide
    except Exception as e:
        logging.error(f"[Agent] Error rendering install guide for {box_dir}: {str(e)}")
        return ""

def list_available_services():
    DOCKER_REFERENCE_PATH = os.path.join(os.getcwd(), "Box")
    services = [
        name for name in os.listdir(DOCKER_REFERENCE_PATH)
        if os.path.isdir(os.path.join(DOCKER_REFERENCE_PATH, name))
    ]
    return services

def startBox(arg: str) -> bytes:
    """Start a box, reusing or assigning ports from port_allocations.json, with netstat safety check."""
    box_dir = os.path.join(os.getcwd(), "Box", arg)
    box_name = box_dir.split("/")[-1]

    # Check if box is already running
    try:
        status = json.loads(checkBoxStatus(box_name).decode())["status"]
        if status == "running":
            logging.info(f"[Agent] Box {box_name} is already running")
            return f"[Agent] Box {box_name} is already running".encode()
    except Exception as e:
        logging.error(f"[Agent] Error checking status for {box_name}: {str(e)}")
        return f"[Agent] Error checking status for {box_name}".encode()

    if not os.path.isdir(box_dir):
        logging.error(f"[Agent] Directory {box_dir} does not exist")
        return f"[Agent] Directory {box_dir} does not exist.".encode()

    # Load port allocations to check if this is the first launch
    allocations = load_port_allocations()
    is_first_launch = box_name not in allocations  # First launch if box_name isn't in allocations yet

    # Check if box already has assigned ports
    if box_name in allocations:
        port_data = allocations[box_name]["port"]
        port = next((p for p in port_data.values() if p != "expose" and p.isdigit()), None)
        if port:
            # Verify assigned port is still free on the system
            cmd = f"netstat -tuln | grep ':{port}'"
            result = run_command(cmd)
            if not result.startswith("[ERROR]") and not result.startswith("[EXCEPTION]") and result:
                logging.error(f"[Agent] Assigned port {port} for {box_name} is in use by another process")
                return f"[Agent] Assigned port {port} for {box_name} is in use by another process".encode()
    else:
        # Assign new port for services requiring external ports
        available_ports = availablePort()
        if not available_ports:
            logging.error(f"[Agent] No available ports for {box_name}")
            return f"[Agent] No available ports for {box_name}".encode()
        port = str(available_ports[0])

        # Update allocations with new port assignments
        docker_compose_path = os.path.join(box_dir, "docker-compose.yml")
        services = extract_service_keys(docker_compose_path)
        port_data = {f"{box_name}_{service}": ("expose" if "db" in service else port) for service in services}
        allocations, port_file = load_port_allocations(write=True)
        allocations[box_name] = {"port": port_data}
        save_port_allocations(allocations, port_file)

    # Replace PORT placeholder in docker-compose.yml
    docker_compose_path = os.path.join(box_dir, "docker-compose.yml")
    with open(docker_compose_path, "r") as f:
        content = f.read()
    content = content.replace("PORT", port)
    with open(docker_compose_path, "w") as f:
        f.write(content)

    try:
        run_command(f"tmux new-session -d -s {box_name} -x 100 -y 1000")
        run_command(f"tmux send-keys -t {box_name} 'cd {box_dir};docker-compose up' C-m")
        sleep(2)
        output = run_command(f"tmux capture-pane -t {box_name} -p")
        logging.info(f"[Agent] Box {box_name} started at port {SHAREHOST}:{port}")

        # If first launch, render and append installGuide.txt
        guide_output = ""
        if is_first_launch:
            guide_output = render_install_guide(box_dir, SHAREHOST, port)
            if guide_output:
                guide_output = "\n\n" + guide_output

        return f"[Agent] Box started at port {SHAREHOST}:{port}\n{guide_output}".encode()
    except subprocess.CalledProcessError as e:
        logging.error(f"[Agent] Error starting docker-compose for {box_name}: {e.output}")
        return f"[Agent] Error starting docker-compose:\n{e.output}".encode()

def stopBox(arg: str) -> bytes:
    """Stop a box, preserving its port assignments and reverting Docker Compose to PORT."""
    box_dir = os.path.join(os.getcwd(), "Box", arg)
    box_name = box_dir.split("/")[-1]

    # Check if box is already stopped
    try:
        status = json.loads(checkBoxStatus(box_name).decode())["status"]
        if status == "stopped":
            logging.info(f"[Agent] Box {box_name} is already stopped")
            return f"[Agent] Box {box_name} is already stopped".encode()
    except Exception as e:
        logging.error(f"[Agent] Error checking status for {box_name}: {str(e)}")
        return f"[Agent] Error checking status for {box_name}".encode()

    if not os.path.isdir(box_dir):
        logging.error(f"[Agent] Directory {box_dir} does not exist")
        return f"[Agent] Directory {box_dir} does not exist.".encode()

    try:
        run_command(f"tmux send-keys -t {box_name} C-c")
        sleep(6)
        run_command(f"tmux send-keys -t {box_name} 'docker-compose down' C-m")
        sleep(6)
        run_command(f"tmux kill-session -t {box_name}")

        # Revert Docker Compose file to use PORT placeholder
        docker_compose_path = os.path.join(box_dir, "docker-compose.yml")
        if not revert_docker_compose_port(docker_compose_path):
            logging.error(f"[Agent] Failed to revert Docker Compose ports for {box_name}")
            return f"[Agent] Box {box_name} stopped, but failed to revert Docker Compose ports".encode()

        logging.info(f"[Agent] Box {box_name} stopped successfully")
        return f"[Agent] Box {box_name} stopped successfully".encode()
    except subprocess.CalledProcessError as e:
        logging.error(f"[Agent] Error stopping box {box_name}: {e.output}")
        return f"[Agent] Error stopping box {box_name}:\n{e.output}".encode()

def revert_docker_compose_port(docker_compose_path: str) -> bool:
    """Revert the ports field in the Docker Compose file to use PORT placeholder."""
    try:
        with open(docker_compose_path, "r") as f:
            content = yaml.safe_load(f)

        # Update ports for services (e.g., wordpress)
        for service, config in content.get("services", {}).items():
            if "ports" in config:
                ports = config["ports"]
                # Replace numeric port mappings (e.g., "10000:80") with "PORT:80"
                config["ports"] = [port if ":" not in port else "PORT:80" if port.endswith(":80") else port for port in
                                   ports]

        # Write back the modified content
        with open(docker_compose_path, "w") as f:
            yaml.safe_dump(content, f, default_flow_style=False)
        logging.info(f"[Agent] Reverted {docker_compose_path} to use PORT placeholder")
        return True
    except Exception as e:
        logging.error(f"[Agent] Error reverting Docker Compose ports in {docker_compose_path}: {str(e)}")
        return False


def deleteBox(arg: str) -> bytes:
    """Delete a box, its port assignments, associated volumes, and prune unused networks."""
    box_dir = os.path.join(os.getcwd(), "Box", arg)
    box_name = box_dir.split("/")[-1]

    # Step 1: Check if box directory exists
    if not os.path.isdir(box_dir):
        logging.error(f"[Agent] Directory {box_dir} does not exist")
        return f"[Agent] Directory {box_dir} does not exist.".encode()

    # Step 2: Check if box is running
    try:
        status = json.loads(checkBoxStatus(box_name).decode())["status"]
        if status == "running":
            # Stop the box if it's running
            logging.info(f"[Agent] Box {box_name} is running, stopping it")
            stop_result = stopBox(box_name)
            if b"Error" in stop_result:
                logging.error(f"[Agent] Failed to stop box {box_name}: {stop_result.decode()}")
                return f"[Agent] Failed to stop box {box_name}: {stop_result.decode()}".encode()
        else:
            logging.info(f"[Agent] Box {box_name} is already stopped")
    except Exception as e:
        logging.error(f"[Agent] Error checking status for {box_name}: {str(e)}")
        return f"[Agent] Error checking status for {box_name}: {str(e)}".encode()

    # Step 3: Remove port allocations
    try:
        allocations, port_file = load_port_allocations(write=True)
        if box_name in allocations:
            del allocations[box_name]
            save_port_allocations(allocations, port_file)
            logging.info(f"[Agent] Removed port allocations for {box_name}")
        else:
            logging.info(f"[Agent] No port allocations found for {box_name}")
    except Exception as e:
        logging.error(f"[Agent] Error removing port allocations for {box_name}: {str(e)}")
        return f"[Agent] Error removing port allocations for {box_name}: {str(e)}".encode()

    # Step 4: Remove Docker volumes starting with boxID.lower()
    try:
        volume_list = run_command("docker volume ls --format '{{.Name}}'")
        if volume_list.startswith("[ERROR]") or volume_list.startswith("[EXCEPTION]"):
            logging.error(f"[Agent] Error listing Docker volumes: {volume_list}")
            return f"[Agent] Error listing Docker volumes: {volume_list}".encode()

        box_id_lower = box_name.lower()
        volumes_to_remove = [vol for vol in volume_list.splitlines() if vol.startswith(box_id_lower)]
        if volumes_to_remove:
            volume_str = " ".join(volumes_to_remove)
            rm_result = run_command(f"docker volume rm {volume_str}")
            if rm_result.startswith("[ERROR]") or rm_result.startswith("[EXCEPTION]"):
                logging.error(f"[Agent] Error removing volumes for {box_name}: {rm_result}")
                return f"[Agent] Error removing volumes for {box_name}: {rm_result}".encode()
            logging.info(f"[Agent] Removed volumes: {volume_str}")
        else:
            logging.info(f"[Agent] No volumes found for {box_name}")
    except Exception as e:
        logging.error(f"[Agent] Error processing volumes for {box_name}: {str(e)}")
        return f"[Agent] Error processing volumes for {box_name}: {str(e)}".encode()

    # Step 5: Prune unused Docker networks
    try:
        prune_result = run_command("docker network prune -f")
        if prune_result.startswith("[ERROR]") or prune_result.startswith("[EXCEPTION]"):
            logging.error(f"[Agent] Error pruning Docker networks: {prune_result}")
            return f"[Agent] Error pruning Docker networks: {prune_result}".encode()
        logging.info(f"[Agent] Pruned unused Docker networks")
    except Exception as e:
        logging.error(f"[Agent] Error pruning networks: {str(e)}")
        return f"[Agent] Error pruning networks: {str(e)}".encode()

    # Step 6: Remove box directory
    try:
        run_command(f"rm -rf {box_dir}")
        logging.info(f"[Agent] Box {box_name} deleted successfully")
        return f"[Agent] Box {box_name} deleted successfully".encode()
    except subprocess.CalledProcessError as e:
        logging.error(f"[Agent] Error deleting box directory {box_name}: {e.output}")
        return f"[Agent] Error deleting box directory {box_name}: {e.output}".encode()
    # """Delete a box and its port assignments."""
    # box_dir = os.path.join(os.getcwd(), "Box", arg)
    # box_name = box_dir.split("/")[-1]
    #
    # if not os.path.isdir(box_dir):
    #     logging.error(f"[Agent] Directory {box_dir} does not exist")
    #     return f"[Agent] Directory {box_dir} does not exist.".encode()
    #
    # # Stop the box first
    # status = json.loads(checkBoxStatus(box_name).decode())["status"]
    # stopBox(arg)
    #
    # # Remove port allocations
    # allocations, port_file = load_port_allocations(write=True)
    # if box_name in allocations:
    #     del allocations[box_name]
    #     save_port_allocations(allocations, port_file)
    #
    # # Remove box directory
    # try:
    #     run_command(f"rm -rf {box_dir}")
    #     logging.info(f"[Agent] Box {box_name} deleted successfully")
    #     return f"[Agent] Box {box_name} deleted successfully".encode()
    # except subprocess.CalledProcessError as e:
    #     logging.error(f"[Agent] Error deleting box {box_name}: {e.output}")
    #     return f"[Agent] Error deleting box {box_name}:\n{e.output}".encode()

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
    return

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

def extract_service_keys(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
        services = data.get('services', {})
        return list(services.keys())

def overviewAgent():
    return run_command(f"docker stats --no-stream --format json").encode()



def checkBoxStatus(box_id: str) -> bytes:
    """Check if a box is running or stopped using docker ps, returning JSON as bytes."""
    try:
        # Run docker ps with filter for box_id and JSON format
        cmd = "docker ps -a --filter \"name="+box_id.lower()+"\" --format \'{{json .}}\'"
        result = run_command(cmd)

        if result.startswith("[ERROR]") or result.startswith("[EXCEPTION]"):
            logging.error(f"[Agent] Error running docker ps for {box_id}: {result}")
            return json.dumps({"boxID": box_id, "status": "stopped", "services": []}).encode()

        # Parse multi-line JSON output
        services = []
        all_running = True
        for line in result.splitlines():
            if line.strip():
                try:
                    container = json.loads(line)
                    service_name = container.get("Names", "")
                    state = container.get("State", "exited")
                    services.append({"name": service_name, "state": state})
                    if state != "running":
                        all_running = False
                except json.JSONDecodeError as e:
                    logging.error(f"[Agent] Error parsing docker ps JSON for {box_id}: {str(e)}")
                    return json.dumps({"boxID": box_id, "status": "stopped", "services": []}).encode()

        # Determine overall box status
        status = "running" if all_running and services else "stopped"
        return json.dumps({"boxID": box_id, "status": status, "services": services}).encode()
    except Exception as e:
        logging.error(f"[Agent] Error checking box status for {box_id}: {str(e)}")
        return json.dumps({"boxID": box_id, "status": "stopped", "services": []}).encode()


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
    ASSIGNABLE_PORTS= o['ports']
    start_agent_listener_InjectionFix()