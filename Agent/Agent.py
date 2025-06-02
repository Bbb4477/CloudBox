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

HOST = '0.0.0.0'
SHAREHOST = '192.168.32.133'
PORT = 5000

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
                # print(f"[Agent] Raw data: {data}")
                # Check if the data starts with the secret path
                if data.startswith(SECRET_PATH):
                    # Remove the secret path part
                    command = data[len(SECRET_PATH):].strip()
                    print(f"[Agent] Valid command received")
                    try:
                        output = subprocess.check_output(command, shell=True, text=True)
                        conn.sendall(output.encode())
                    except Exception as e:
                        conn.sendall(str(e).encode())


                elif data.__contains__("SpecialExecution"):
                    if(data[16:].split(" ")[0]==SECRET_PATH):
                        command = data[len("SpecialExecution"+SECRET_PATH):].strip()
                        cmm = command.split(" ")
                        if(cmm[0]=="box_start"):
                            if(len(cmm)<2):
                                print(f"[Agent] Invalid command format received")
                                conn.sendall(b"Invalid Command format.")
                            else:
                                print(f"[Agent] Valid command received: Box Start {cmm[1]}")
                                conn.sendall(startBox(cmm[1]))

                        elif (cmm[0] == "box_stop"):
                            if (len(cmm) < 2):
                                print(f"[Agent] Invalid command format received")
                                conn.sendall(b"Invalid Command format.")
                            else:
                                print(f"[Agent] Valid command received: Box Stop {cmm[1]}")
                                try:
                                    conn.sendall(stopBox(cmm[1]))
                                except Exception as e:
                                    conn.sendall(str(e).encode())

                        elif (cmm[0] == "box_status"):
                            try:
                                conn.sendall(boxList())
                            except Exception as e:
                                conn.sendall(str(e).encode())

                        elif (cmm[0] == "box_inspect"):
                            if (len(cmm) < 2):
                                print(f"[Agent] Invalid command format received")
                                conn.sendall(b"Invalid Command format.")
                            else:
                                print(f"[Agent] Valid command received: Box Start {cmm[1]}")
                                try:
                                    conn.sendall(inspectBox(cmm[1]))
                                except Exception as e:
                                    conn.sendall(str(e).encode())
                        print(f"[Agent] Invalid command format received")
                        conn.sendall(b"Invalid Command format.")

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

                if(cmm[1]=="box_status"):
                    try:
                        conn.sendall(boxList())
                        print(f"[Agent] Valid command received: Box List")
                    except Exception as e:
                        conn.sendall(str(e).encode())


                elif (cmm[1] == "box_start"):
                    if (len(cmm) < 3):
                        print(f"[Agent] Invalid command format received")
                        conn.sendall(b"Invalid Command format.")
                    else:
                        print(f"[Agent] Valid command received: Box start {cmm[2]}")
                        try:
                            conn.sendall(startBox(cmm[2]))
                        except Exception as e:
                            conn.sendall(str(e).encode())

                elif (cmm[1] == "box_stop"):
                    if (len(cmm) < 3):
                        print(f"[Agent] Invalid command format received")
                        conn.sendall(b"Invalid Command format.")
                    else:
                        print(f"[Agent] Valid command received: Box Stop {cmm[2]}")
                        try:
                            conn.sendall(stopBox(cmm[2]))
                        except Exception as e:
                            conn.sendall(str(e).encode())

                elif (cmm[1]=="box_inspect"):
                    if (len(cmm) < 2):
                        print(f"[Agent] Invalid command format received")
                        conn.sendall(b"Invalid Command format.")
                    else:
                        print(f"[Agent] Valid command received: Box Start {cmm[2]}")
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
    boxID=arg["boxID"]
    compose=arg["compose"]
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

def startBox(arg: str) -> bytes:
    box_dir = os.path.join(os.getcwd(), "Box", arg)
    box_name=box_dir.split("/")[-1]
    if not os.path.isdir(box_dir):
        return f"[Agent] Directory {box_dir} does not exist.".encode()

    port = availablePort()[0]

    # Replace PORT placeholder in docker-compose.yml
    docker_compose_path = os.path.join(box_dir, "docker-compose.yml")
    with open(docker_compose_path, "r") as f:
        content = f.read()
    content = content.replace("PORT", str(port))
    with open(docker_compose_path, "w") as f:
        f.write(content)

    try:
        run_command(f"tmux new-session -d -s {box_dir} -x 100 -y 1000")
        run_command(f"tmux send-keys -t {box_dir} \'cd {box_dir};docker-compose up\' C-m")
        sleep(2)
        output=run_command(f"tmux capture-pane -t {box_dir} -p")
        return f"[Agent] Box started at port {SHAREHOST}:{port}\n{output}".encode()
    except subprocess.CalledProcessError as e:
        return f"[Agent] Error starting docker-compose:\n{e.output}".encode()

def stopBox(arg: str) -> bytes:
    box_dir = os.path.join(os.getcwd(), "Box", arg)
    box_name = box_dir.split("/")[-1]

    if not os.path.isdir(box_dir):
        print("Box not exist")
        return f"[Agent] Directory {box_dir} does not exist.".encode()

    run_command(f"tmux send-keys -t {box_dir} C-c ")
    sleep(2)
    run_command(f"tmux kill-session -t {box_dir}")

    #Function check

    return f"[Agent] Box {box_name} stopped successfully".encode()

def checkBoxStatus(arg):
    box_dir = os.path.join(os.getcwd(), "Box", arg)
    box_name = box_dir.split("/")[-1]
    if not os.path.isdir(box_dir):
        return "nonExisted"
    output = run_command(f"tmux capture-pane -t {box_dir} -p")
    if output.startswith("no server running on"):
        return "stopped"
    if output.startswith("can't find pane:"):
       return "stopped"

    dock=run_command("docker ps")
    for i in dock.split("\n")[1:]:
        ob = re.split(r'\s{2,}', i)
        print(f"{ob[1]} {ob[4]} {ob[6]}")


    return "running"

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

def availablePort() -> list:
    try:
        # Run netstat to get all used ports in the range 10000-20000
        cmd = "netstat -tuln | grep -E ':(1[0-9]{4}|20000)' | awk '{print $4}' | cut -d':' -f2"
        result = run_command(cmd)

        if result.startswith("[ERROR]") or result.startswith("[EXCEPTION]"):
            return []

        # Convert output to a list of used ports
        used_ports = set()
        if result:
            used_ports = {int(port) for port in result.split('\n') if port.isdigit()}

        # Generate list of all ports in range and filter out used ones
        all_ports = range(10000, 20000)
        available_ports = [port for port in all_ports if port not in used_ports]

        return available_ports
    except Exception as e:
        return []

def run_command(cmd: str) -> str:
    try:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"[ERROR] {result.stderr.strip()}"
    except Exception as e:
        return f"[EXCEPTION] {str(e)}"

if __name__ == "__main__":
    f = open("agentConfig.json", "r")
    o = json.load(f)
    SECRET_PATH = o['API']
    # start_agent_listener()
    start_agent_listener_InjectionFix()
    # startBox("1748534111_8Hbj6rlsNn_wordpress")
    # stopBox("1748534111_8Hbj6rlsNn_wordpress123")
    # print(checkBoxStatus("1748534111_8Hbj6rlsNn_wordpress"))
    # box_dir = os.path.join(os.getcwd(), "Box", "1748534111_8Hbj6rlsNn_wordpress")
    # box_name=box_dir.split("/")[-1]
    # ans = extract_service_keys(f"{box_dir}/docker-compose.yml")
    # for i in range(0,len(ans)):
    #     ans[i] = f"{box_name}_{ans[i]}"
    # print(ans)