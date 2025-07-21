
from flask import Flask, jsonify, request, Response, send_file  # Added send_file
import json
import socket
import os
import re
from pathlib import Path
import time
import random
import string
import subprocess
from time import sleep
import requests
import base64
from flask_cors import CORS
import logging
import fcntl
import secrets
import shutil
import tarfile
import hashlib
from dotenv import load_dotenv

app = Flask(__name__)

CORS(app)

def generate_box_id(length: int = 10) -> str:
    timestamp = int(time.time())
    rand_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return f"{timestamp}_{rand_suffix}"

def extract_variables_from_compose(file_path):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist.")

    with open(path, 'r') as file:
        content = file.read()

    # Find all unique placeholders in curly braces
    variables = re.findall(r'\{([^}]+)\}', content)
    return sorted(set(variables))

def randomGen(f:str):
    if 'p' in f:
        return portAssign()

    chars = ''
    if 't' in f:
        chars += string.ascii_letters
    if 'd' in f:
        chars += string.digits

    # Extract number at the end (length)
    length = int(''.join(filter(str.isdigit, f)))

    if not chars or length <= 0:
        raise ValueError("Invalid format string.")

    return ''.join(random.choice(chars) for _ in range(length))

def portAssign():
    return "PORT"

def variableGen(inp):
    f = open("DockerFilesReference/RenderFormula.txt", "r")
    formula = []
    for i in f:
        formula.append(i.split(","))
    for i in formula:
        i[1]=i[1].replace("\n","")
    ans=[]
    for i in inp:
        for j in formula:
            if str(i).__contains__(str(j[0])):
                ans.append([i,randomGen(j[1])])
    return ans

def find(lst, x):
    for i in range(0,len(lst)):
        if lst[i]==x:
            return i
    return -1

def run_command(cmd: str) -> str:
    try:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"[ERROR] {result.stderr.strip()}"
    except Exception as e:
        return f"[EXCEPTION] {str(e)}"

def createNewBox(arg):
    commands=""
    thisPath=run_command("pwd")
    service = list_available_services()
    ans={
        "commands": []
    }
    if arg == "default":
        while (True):
            inp = input("Input your service pick: ")
            if find(service, inp) != -1:
                break
            if (inp == ""):
                return
            print("service not found")
        arg = inp

    elif find(service, arg) == -1:
        return

    ThisBox = generate_box_id()
    ans["commands"].append(f"cd Box; mkdir {ThisBox}_{arg}")

    targetPath=thisPath+"/DockerFilesReference/"+arg+"/docker-compose.yml"
    f = open(targetPath, "r")
    st = ""
    for i in f:
        st += i
    compose=render(st,variableGen(extract_variables_from_compose(targetPath)))
    composepath=thisPath+"/box/"+ThisBox+"_"+arg+"/docker-compose.yml"
    # o=open(composepath,"w")
    # o.write(compose)
    ans["commands"].append(f"cd Box; cd {ThisBox}_{arg}; echo \"{compose}\" > docker-compose.yml;")
    ans["commands"].append(f"cat Box/{ThisBox}_{arg}/docker-compose.yml")
    return ans

def createNewBoxNoDirectCommand(arg):
    commands = ""
    thisPath = run_command("pwd")
    service = list_available_services()

    jDeclare = '{"boxID": "", "compose": "", "installGuide": ""}'
    ans = json.loads(jDeclare)

    if find(service, arg) == -1:
        return

    ans["boxID"] = f"{generate_box_id()}_{arg}"
    targetPath = thisPath + "/DockerFilesReference/" + arg + "/docker-compose.yml"
    f = open(targetPath, "r")
    st = ""
    for i in f:
        st += i
    compose = render(st, variableGen(extract_variables_from_compose(targetPath)))
    ans["compose"] = compose
    # Add installGuide.txt if it exists
    guide_path = thisPath + "/DockerFilesReference/" + arg + "/installGuide.txt"
    if os.path.exists(guide_path):
        with open(guide_path, "r") as f:
            ans["installGuide"] = f.read()
    return ans

def find_available_ports(lower: int, upper: int, count: int = 1) -> list:
    used_ports = set()

    # Run netstat to get list of used ports
    output = run_command("netstat -tuln")

    # Extract all numeric ports from the output
    matches = re.findall(r':(\d+)', output)
    for port in matches:
        used_ports.add(int(port))
    available_ports = []
    for port in range(lower, upper + 1):
        if port not in used_ports:
            available_ports.append(port)

    return available_ports

def render(source, variables):
    """Render a source string by replacing placeholders with values from a list of [key, value] pairs."""
    rendered = source
    # Convert list of [key, value] pairs to a dictionary
    var_dict = {k: v for k, v in variables}
    for key, value in var_dict.items():
        placeholder = f"{{{key}}}"
        rendered = rendered.replace(placeholder, str(value))
    return rendered

def stats(arg):
    return

def serviceStats(arg):
    return

def send_command(agent_ip, agent_port, command, secret):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((agent_ip, agent_port))
        # Prepend secret path
        payload = f"{secret} {command}"
        s.sendall(payload.encode())
        output = s.recv(4096).decode()
        return output

def send_command_LoopUntilFinish(host, payload, secret):
    # Check agent status before attempting socket communication
    if not check_agent_status(host):
        return f"Connection error: {host} is disconnected or stopped"
    json_str = json.dumps(payload)
    b64_command = base64.b64encode(json_str.encode()).decode()
    payload = f"{secret} {len(b64_command)} {b64_command}"
    try:
        # Split host into address and port
        address, port_str = host.rsplit(":", 1)
        port = int(port_str)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((address, port))
            s.sendall(payload.encode())
            output = s.recv(4096).decode()
        return output
    except (ConnectionRefusedError, socket.timeout, socket.gaierror, ValueError, OSError) as e:
        return f"Connection error: {str(e)}"

def check_agent_status(host):
    try:
        # Split host into address and port
        address, port_str = host.rsplit(":", 1)
        port = int(port_str)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect((address, port))
            return True
    except (ConnectionRefusedError, socket.timeout, OSError, ValueError):
        return False

def check_api(api_key, creds_data):
    if api_key in creds_data['admins'].values():
        return "admin"
    for agent in creds_data['agents'].values():
        if agent['API'] == api_key:
            return "agent"
    return None

def socketSend(host, payload):
    # Check agent status before attempting socket communication
    if not check_agent_status(host):
        return f"Connection error: {host} is disconnected or stopped"
    try:
        # Split host into address and port (e.g., "192.168.32.132:5000" -> "192.168.32.132", 5000)
        address, port_str = host.rsplit(":", 1)
        port = int(port_str)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # s.settimeout(2)  # Set timeout for connection
            # Resolve address (supports domains and IPs)
            resolved_address = socket.gethostbyname(address)
            s.connect((resolved_address, port))
            s.sendall(payload.encode())
            output = s.recv(4096).decode()
            return output
    except (ConnectionRefusedError, socket.timeout, socket.gaierror, ValueError, OSError) as e:
        return f"Connection error: {str(e)}"

@app.route('/<api_key>/agent/list', methods=['POST'])
def listAgent(api_key):
    creds=load_creds()
    if check_api(api_key, creds) == "admin":
        ans = {}
        for agent_id, agent_info in creds["agents"].items():
            ans[agent_id] = {
                "host": agent_info["host"],
                "description": agent_info["description"],
                "status": "connected" if check_agent_status(agent_info["host"]) else "disconnected"
            }
        return jsonify(json.dumps(ans))
    return jsonify("Invalid API key.")

@app.route('/<api_key>/agent/listGet', methods=['GET'])
def listAgentGet(api_key):
    creds = load_creds()
    if check_api(api_key, creds) == "admin":
        ans = {}
        for agent_id, agent_info in creds["agents"].items():
            ans[agent_id] = {
                "host": agent_info["host"],
                "description": agent_info["description"],
                "status": "connected" if check_agent_status(agent_info["host"]) else "disconnected"
            }
        return jsonify(json.dumps(ans))
    return jsonify("Invalid API key.")

def listAgent() -> list:
    creds = load_creds()
    ans=[]
    for i in creds["agents"]:
        ans.append(i)
    return ans

@app.route('/<api_key>/agent/box/list', methods=['POST'])
def boxListAPI(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        data = request.get_json()
        if not data or "agentID" not in data:
            return jsonify({"error": "Missing agentID in JSON body"}), 400
        agentID = data["agentID"]
        if find(listAgent(), agentID) == -1:
            return jsonify("Invalid AgentID")
        return jsonify(boxList(agentID))
    return jsonify("Invalid API key.")

def boxList(agentID):
    creds_data = load_creds()
    payload = creds_data["agents"][agentID]["API"] + " box_status"
    result = socketSend(creds_data["agents"][agentID]["host"], payload)
    if result.startswith("Connection error:"):
        return result
    return result.split(' ')

@app.route('/<api_key>/agent/box/stats', methods=['POST'])
def boxStatus(api_key):
    return

def boxStatus(agentID,boxID):
    return

@app.route('/<api_key>/agent/box/start', methods=['POST'])
def boxStartAPI(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        data = request.get_json()
        if not data or "agentID" not in data:
            return jsonify({"error": "Missing agentID in JSON body"}), 400
        if not data or "boxID" not in data:
            return jsonify({"error": "Missing boxID in JSON body"}), 400
        agentID = data["agentID"]
        if find(listAgent(), agentID) == -1:
            return jsonify("Invalid AgentID")
        boxID = data["boxID"]
        if find(boxList(agentID), boxID) == -1:
            return jsonify("Invalid BoxID")
        return jsonify(boxStart(agentID, boxID))
    return jsonify("Invalid API key.")

def boxStart(agentID, boxID):
    creds_data = load_creds()
    secret = creds_data["agents"][agentID]["API"]
    payload = f"{secret} box_start {boxID}"
    return socketSend(creds_data["agents"][agentID]["host"], payload)

@app.route('/<api_key>/agent/box/stop', methods=['POST'])
def boxStopAPI(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        data = request.get_json()
        if not data or "agentID" not in data:
            return jsonify({"error": "Missing agentID in JSON body"}), 400
        if not data or "boxID" not in data:
            return jsonify({"error": "Missing boxID in JSON body"}), 400
        agentID = data["agentID"]
        if find(listAgent(), agentID) == -1:
            return jsonify("Invalid AgentID")
        boxID = data["boxID"]
        if find(boxList(agentID), boxID) == -1:
            return jsonify("Invalid BoxID")
        return jsonify(boxStop(agentID, boxID))
    return jsonify("Invalid API key.")

def boxStop(agentID, boxID):
    creds_data = load_creds()
    secret = creds_data["agents"][agentID]["API"]
    payload = f"{secret} box_stop {boxID}"
    return socketSend(creds_data["agents"][agentID]["host"], payload)

@app.route('/<api_key>/agent/box/delete', methods=['POST'])
def boxDeleteAPI(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        data = request.get_json()
        if not data or "agentID" not in data:
            return jsonify({"error": "Missing agentID in JSON body"}), 400
        if not data or "boxID" not in data:
            return jsonify({"error": "Missing boxID in JSON body"}), 400
        agentID = data["agentID"]
        if find(listAgent(), agentID) == -1:
            return jsonify("Invalid AgentID")
        boxID = data["boxID"]
        if find(boxList(agentID), boxID) == -1:
            return jsonify("Invalid BoxID")
        return jsonify(boxDelete(agentID, boxID))
    return jsonify("Invalid API key.")

def boxDelete(agentID, boxID):
    creds_data = load_creds()
    secret = creds_data["agents"][agentID]["API"]
    payload = f"{secret} box_delete {boxID}"
    return socketSend(creds_data["agents"][agentID]["host"], payload)

@app.route('/<api_key>/agent/box/backup', methods=['POST'])
def boxBackupAPI(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        data = request.get_json()
        if not data or "agentID" not in data:
            return jsonify({"error": "Missing agentID in JSON body"}), 400
        if not data or "boxID" not in data:
            return jsonify({"error": "Missing boxID in JSON body"}), 400
        if not data or "backupType" not in data:
            return jsonify({"error": "Missing backupType in JSON body"}), 400
        agentID = data["agentID"]
        if find(listAgent(), agentID) == -1:
            return jsonify("Invalid AgentID")
        boxID = data["boxID"]
        if find(boxList(agentID), boxID) == -1:
            return jsonify("Invalid BoxID")
        backupType=data["backupType"]
        if backupType == "full":
            return jsonify(boxBackupFull(agentID, boxID))
        elif backupType == "data":
            return jsonify(boxBackupData(agentID, boxID))
        else:
            return jsonify(f"Backup type {backupType} not found")
    return jsonify("Invalid API key.")

def boxBackupFull(agentID, boxID):
    creds_data = load_creds()
    secret = creds_data["agents"][agentID]["API"]
    payload = f"{secret} box_backupFull {boxID}"
    return socketSend(creds_data["agents"][agentID]["host"], payload)

def boxBackupData(agentID, boxID):
    creds_data = load_creds()
    secret = creds_data["agents"][agentID]["API"]
    payload = f"{secret} box_backupData {boxID}"
    return socketSend(creds_data["agents"][agentID]["host"], payload)

@app.route('/<api_key>/agent/box/restore', methods=['POST'])
def boxRestoreAPI(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        data = request.get_json()
        if not data or "agentID" not in data:
            return jsonify({"error": "Missing agentID in JSON body"}), 400
        if not data or "boxID" not in data:
            return jsonify({"error": "Missing boxID in JSON body"}), 400
        if not data or "backupType" not in data:
            return jsonify({"error": "Missing backupType in JSON body"}), 400
        if not data or "backupID" not in data:
            return jsonify({"error": "Missing backupID in JSON body"}), 400
        agentID = data["agentID"]
        if find(listAgent(), agentID) == -1:
            return jsonify("Invalid AgentID")
        boxID = data["boxID"]
        if find(boxList(agentID), boxID) == -1:
            return jsonify("Invalid BoxID")
        backupID = data["backupID"]
        if find(boxListBackup(agentID,boxID), backupID) == -1:
            return jsonify("Invalid backupID")
        backupType=data["backupType"]
        if backupType == "full":
            return jsonify(boxRestoreFull(agentID, boxID, backupID))
        elif backupType == "data":
            return jsonify(boxRestoreData(agentID, boxID, backupID))
        else:
            return jsonify(f"Backup type {backupType} not found")
    return jsonify("Invalid API key.")

def boxRestoreFull(agentID, boxID, backupID):
    return socketSend("Didn't do anything")

def boxRestoreData(agentID, boxID, backupID):
    creds_data = load_creds()
    secret = creds_data["agents"][agentID]["API"]
    payload = f"{secret} box_restoreData {boxID} {backupID}"
    return socketSend(creds_data["agents"][agentID]["host"], payload)

@app.route('/<api_key>/agent/box/backup/remove', methods=['POST'])
def boxBackupRemoveAPI(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        data = request.get_json()
        if not data or "agentID" not in data:
            return jsonify({"error": "Missing agentID in JSON body"}), 400
        if not data or "boxID" not in data:
            return jsonify({"error": "Missing boxID in JSON body"}), 400
        if not data or "backupID" not in data:
            return jsonify({"error": "Missing backupID in JSON body"}), 400
        agentID = data["agentID"]
        if find(listAgent(), agentID) == -1:
            return jsonify("Invalid AgentID")
        boxID = data["boxID"]
        if find(boxList(agentID), boxID) == -1:
            return jsonify("Invalid BoxID")
        backupID = data["backupID"]
        if find(boxListBackup(agentID,boxID), backupID) == -1:
            return jsonify("Invalid backupID")
        return jsonify(boxBackupRemove(agentID, boxID, backupID))
    return jsonify("Invalid API key.")

def boxBackupRemove(agentID, boxID, backupID):
    creds_data = load_creds()
    secret = creds_data["agents"][agentID]["API"]
    payload = f"{secret} backup_remove {boxID} {backupID}"
    return socketSend(creds_data["agents"][agentID]["host"], payload)

@app.route('/<api_key>/agent/box/backup/list', methods=['POST'])
def boxListBackupAPI(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        data = request.get_json()
        if not data or "agentID" not in data:
            return jsonify({"error": "Missing agentID in JSON body"}), 400
        if not data or "boxID" not in data:
            return jsonify({"error": "Missing boxID in JSON body"}), 400
        agentID = data["agentID"]
        if find(listAgent(), agentID) == -1:
            return jsonify("Invalid AgentID")
        boxID = data["boxID"]
        if find(boxList(agentID), boxID) == -1:
            return jsonify("Invalid BoxID")
        return jsonify(boxListBackup(agentID, boxID))
    return jsonify("Invalid API key.")

def boxListBackup(agentID, boxID):
    creds_data = load_creds()
    secret = creds_data["agents"][agentID]["API"]
    payload = f"{secret} list_backup {boxID}"
    return socketSend(creds_data["agents"][agentID]["host"], payload).split(" ")

@app.route('/<api_key>/agent/status', methods=['POST'])
def agentStatusAPI(api_key):
    return

def agentStatus(agentID):
    return

@app.route('/<api_key>/agent/inspect', methods=['POST'])
def inspectAgent(api_key):
    creds_data = load_creds()
    data = request.get_json()
    if not data or "agentID" not in data:
        return jsonify({"error": "Missing agentID in JSON body"}), 400
    agentID = data["agentID"]
    if check_api(api_key, creds_data) == "admin":
        if find(listAgent(), agentID) != -1:
            return jsonify(creds_data["agents"][agentID])
        return jsonify("Invalid AgentID")
    return jsonify("Invalid API key.")

@app.route('/<api_key>/server/availableService', methods=['POST'])
def listServices(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        DOCKER_REFERENCE_PATH = run_command("pwd") + "/DockerFilesReference"
        services = [
            name for name in os.listdir(DOCKER_REFERENCE_PATH)
            if os.path.isdir(os.path.join(DOCKER_REFERENCE_PATH, name))
        ]
        return jsonify(services)
    return jsonify("Invalid API key.")

@app.route('/<api_key>/server/availableServiceGet', methods=['GET'])
def listServicesGet(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        DOCKER_REFERENCE_PATH = run_command("pwd") + "/DockerFilesReference"
        services = [
            name for name in os.listdir(DOCKER_REFERENCE_PATH)
            if os.path.isdir(os.path.join(DOCKER_REFERENCE_PATH, name))
        ]
        return jsonify(services)
    return jsonify("Invalid API key.")

def list_available_services():
    DOCKER_REFERENCE_PATH=run_command("pwd")+"/DockerFilesReference"
    services = [
        name for name in os.listdir(DOCKER_REFERENCE_PATH)
        if os.path.isdir(os.path.join(DOCKER_REFERENCE_PATH, name))
    ]
    return services

@app.route('/<api_key>/agent/box/install', methods=['POST'])
def ApplyBoxAPI(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        data = request.get_json()
        if not data or "agentID" not in data:
            return jsonify({"error": "Missing agentID in JSON body"}), 400
        if not data or "service" not in data:
            return jsonify({"error": "Missing service in JSON body"}), 400
        agentID = data["agentID"]
        if find(listAgent(), agentID) == -1:
            return jsonify("Invalid AgentID")
        service = data["service"]
        return jsonify(ApplyBoxNoInjection(service, agentID))
    return jsonify("Invalid API key.")

def ApplyBoxNoInjection(service, agentID):
    creds_data = load_creds()
    if find(listAgent(), agentID) == -1:
        return "Error, no Agent available"
    if find(list_available_services(), service) == -1:
        return f"No {service} currently available in template stores"
    payload = createNewBoxNoDirectCommand(service)
    return send_command_LoopUntilFinish(creds_data["agents"][agentID]["host"], payload, creds_data["agents"][agentID]["API"])

@app.route('/<api_key>/agent/overview', methods=['POST'])
def AgentOverview(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        data = request.get_json()
        if not data or "agentID" not in data:
            return jsonify({"error": "Missing agentID in JSON body"}), 400
        agentID = data["agentID"]
        if find(listAgent(), agentID) == -1:
            return jsonify("Invalid AgentID")
        return jsonify(AgentOverview(agentID))
    return jsonify("Invalid API key.")

def AgentOverview(agentID):
    creds_data = load_creds()
    secret = creds_data["agents"][agentID]["API"]
    payload = f"{secret} agent_stats"
    return socketSend(creds_data["agents"][agentID]["host"], payload)

@app.route('/<api_key>/agent/create', methods=['POST'])
def AgentCreateAPI(api_key):
    """Create a new agent, generate its configuration, and provide a download URL."""
    if check_api(api_key, load_creds()) != "admin":
        return jsonify({"error": "Invalid API key."}), 403

    data = request.get_json()
    required_fields = ["description", "host", "ports"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing {field} in JSON body"}), 400

    description = data["description"]
    host = data["host"]
    listen_port = int(host.rsplit(":")[1]) # data["listenPort"]
    ports = data["ports"]
    sharehost = data.get("sharehost", "")

    # Validate host format (IP or domain with port)
    try:
        host_part, port_part = host.rsplit(":", 1)
        int(port_part)  # Ensure port is numeric
        if not host_part:  # Ensure host part is not empty
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid host format. Expected IP:port or domain:port"}), 400

    # Validate listenPort is numeric
    try:
        listen_port = int(listen_port)
    except ValueError:
        return jsonify({"error": "Invalid listenPort. Must be a number"}), 400

    creds = load_creds()
    agent_id = get_next_agent_id(creds)
    api_key_generated = generate_api_key()

    timestamp_random = generate_box_id()
    directory_name = f"{timestamp_random}_{agent_id}"
    agent_dir = os.path.join("agents", "agentDynamic", directory_name)

    template_dir = os.path.join("agents", "agentTemplate")
    try:
        shutil.copytree(template_dir, agent_dir)
    except Exception as e:
        return jsonify({"error": f"Failed to create agent directory: {str(e)}"}), 500

    # Update agentConfig.json
    agent_config_path = os.path.join(agent_dir, "agentConfig.json")
    try:
        with open(agent_config_path, 'r') as f:
            agent_config = json.load(f)
        agent_config["API"] = api_key_generated
        agent_config["listenPort"] = str(listen_port)
        agent_config["ports"] = ports
        agent_config["sharehost"] = sharehost
        with open(agent_config_path, 'w') as f:
            json.dump(agent_config, f, indent=4)
    except Exception as e:
        return jsonify({"error": f"Failed to update agentConfig.json: {str(e)}"}), 500

    # Create empty port_allocations.json
    port_allocations_path = os.path.join(agent_dir, "Box", "port_allocations.json")
    try:
        with open(port_allocations_path, 'w') as f:
            json.dump({}, f, indent=4)
    except Exception as e:
        return jsonify({"error": f"Failed to create port_allocations.json: {str(e)}"}), 500

    # Update creds.json
    creds["agents"][agent_id] = {
        "host": host,
        "description": description,
        "API": api_key_generated
    }
    try:
        save_creds(creds)
    except Exception as e:
        return jsonify({"error": f"Failed to update creds.json: {str(e)}"}), 500

    # Create tar.gz archive
    archive_name = f"{directory_name}.tar.gz"
    archive_path = os.path.join("agents", "agentDynamic", archive_name)
    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(agent_dir, arcname=os.path.basename(agent_dir))
    except Exception as e:
        return jsonify({"error": f"Failed to create archive: {str(e)}"}), 500

    # Generate download URL using server IP and port
    server_host = request.host
    download_url = f"http://{server_host}/{api_key}/agents/agentDynamic/{archive_name}"
    #download_url = f"{sharehost}/{api_key}/agents/agentDynamic/{archive_name}"
    load_creds()
    return jsonify(json.dumps({
        "agentID": agent_id,
        "downloadUrl": download_url,
        "message": "Agent created successfully"
    }))

@app.route('/<api_key>/agent/modify', methods=['POST'])
def AgentModifyAPI(api_key):
    return

@app.route('/<api_key>/agent/remove', methods=['POST'])
def AgentRemoveAPI(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) != "admin":
        return jsonify({"error": "Invalid API key."}), 403

    data = request.get_json()
    if not data or "agentID" not in data:
        return jsonify({"error": "Missing agentID in JSON body"}), 400

    agent_id = data["agentID"]
    if agent_id not in creds_data["agents"]:
        return jsonify({"error": "Invalid AgentID"}), 400

    try:
        del creds_data["agents"][agent_id]
        save_creds(creds_data)
        return jsonify({"message": f"Agent {agent_id} removed successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to remove agent {agent_id}: {str(e)}"}), 500

@app.route('/<api_key>/login', methods=['POST'])
def loginCredentials(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) != "admin":
        return jsonify({"error": "Invalid API key."}), 403

    data = request.get_json()
    if not data or "username" not in data:
        return jsonify({"error": "Missing username in JSON body"}), 400
    if not data or "password" not in data:
        return jsonify({"error": "Missing password in JSON body"}), 400

    username = data["username"]
    if username not in creds_data["credentials"]:
        return jsonify("fail")

    input_password = data["password"]
    hashed_input = hashlib.sha256(input_password.encode()).hexdigest()
    stored_password = creds_data["credentials"][username]["password"]

    if hashed_input == stored_password:
        return jsonify("success")
    return jsonify("fail")

# @app.route('/<api_key>/agent/connectBox', methods=['POST'])
# def proxyConnectAPI(api_key):
#     creds_data = load_creds()
#     if check_api(api_key, creds_data) == "admin":
#         data = request.get_json()
#         if not data or "agentID" not in data or "boxID" not in data:
#             return jsonify({"error": "Missing agentID or boxID in JSON body"}), 400
#
#         agent_id = data["agentID"]
#         box_id = data["boxID"]
#
#         if agent_id not in creds_data["agents"]:
#             return jsonify("Invalid AgentID"), 400
#
#         overview = AgentOverview(agent_id)
#         if overview.startswith("Connection error:"):
#             return jsonify({"error": overview}), 500
#
#         try:
#             overview_data = json.loads(overview)
#             if box_id not in overview_data or overview_data[box_id]["status"] != "running":
#                 return jsonify({"error": "Box not found or not running"}), 400
#         except json.JSONDecodeError:
#             return jsonify({"error": "Invalid response from agent"}), 500
#
#         secret = creds_data["agents"][agent_id]["API"]
#         payload = f"{secret} get_port {box_id}"
#         port_response = socketSend(creds_data["agents"][agent_id]["host"], payload)
#         if port_response.startswith("Connection error:"):
#             return jsonify({"error": port_response}), 500
#
#         try:
#             port_data = json.loads(port_response)
#             if "port" not in port_data or not port_data["port"]:
#                 return jsonify({"error": "Failed to retrieve box port"}), 500
#             box_port = port_data["port"]
#         except json.JSONDecodeError:
#             return jsonify({"error": "Invalid port response from agent"}), 500
#
#         proxy_port = availableProxyPort()
#         if proxy_port is None:
#             return jsonify({"error": "No available proxy ports"}), 503
#
#         nginx_box_id = f"nginx_{agent_id}_{box_id}_{proxy_port}"
#         agent_ip = creds_data["agents"][agent_id]["host"].split(":")[0]
#         variables = {
#             "Export_port": proxy_port,
#             "agent_ip": agent_ip,
#             "agent_port": box_port
#         }
#         compose_template = open("DockerFilesReference/nginx/docker-compose.yml", "r").read()
#         compose = render(compose_template, variables)
#         nginx_conf_template = open("DockerFilesReference/nginx/nginx.conf", "r").read()
#         nginx_conf = render(nginx_conf_template, variables)
#
#         arg = {"boxID": nginx_box_id, "compose": compose, "nginx_conf": nginx_conf}
#         create_result = createNewBoxAgent(arg)
#         if create_result.startswith("[EXCEPTION]"):
#             return jsonify({"error": create_result}), 500
#
#         start_result = startBox(nginx_box_id)
#         if start_result.startswith("[Server] Error"):
#             return jsonify({"error": start_result}), 500
#
#         creds_data["proxy"]["allocation"][nginx_box_id] = {
#             "host": f"{agent_ip}:{box_port}",
#             "agentID": agent_id,
#             "boxID": box_id,
#             "status": "running"
#         }
#         save_creds(creds_data)
#
#         proxy_url = f"http://{request.host}/{api_key}/{agent_id}/{box_id}"
#         return jsonify({"proxy_url": proxy_url})
#     return jsonify("Invalid API key."), 403
#
# @app.route('/<api_key>/agent/disconnectBox', methods=['POST'])
# def proxyDisconnectAPI(api_key):
#     creds_data = load_creds()
#     if check_api(api_key, creds_data) == "admin":
#         data = request.get_json()
#         if not data or "agentID" not in data or "boxID" not in data:
#             return jsonify({"error": "Missing agentID or boxID in JSON body"}), 400
#
#         agent_id = data["agentID"]
#         box_id = data["boxID"]
#
#         if agent_id not in creds_data["agents"]:
#             return jsonify("Invalid AgentID"), 400
#
#         allocation = creds_data["proxy"].get("allocation", {})
#         for nginx_box_id, data in allocation.items():
#             if data["agentID"] == agent_id and data["boxID"] == box_id and data["status"] == "running":
#                 stop_result = stopBox(nginx_box_id)
#                 if stop_result.startswith("[Server] Error"):
#                     return jsonify({"error": stop_result}), 500
#
#                 creds_data["proxy"]["allocation"][nginx_box_id]["status"] = "stopped"
#                 save_creds(creds_data)
#                 return jsonify({"message": f"Proxy for {box_id} stopped"})
#
#         return jsonify({"error": "No running proxy found for the specified agent and box"}), 404
#     return jsonify("Invalid API key."), 403
#
# @app.route('/<api_key>/<agentID>/<boxID>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
# @app.route('/<api_key>/<agentID>/<boxID>', methods=['GET', 'POST', 'PUT', 'DELETE'])
# def proxy_request(api_key, agentID, boxID, path=None):
#     creds_data = load_creds()
#     if check_api(api_key, creds_data) != "admin":
#         return jsonify("Invalid API key."), 403
#
#     allocation = creds_data["proxy"].get("allocation", {})
#     for nginx_box_id, data in allocation.items():
#         if data["agentID"] == agentID and data["boxID"] == boxID and data["status"] == "running":
#             port = int(nginx_box_id.split("_")[-1])
#             url = f"http://localhost:{port}/{path}" if path else f"http://localhost:{port}/"
#             method = request.method
#             headers = {key: value for key, value in request.headers if key != 'Host'}
#             resp = requests.request(
#                 method=method,
#                 url=url,
#                 headers=headers,
#                 data=request.get_data(),
#                 cookies=request.cookies,
#                 allow_redirects=False
#             )
#             excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
#             headers = [(name, value) for (name, value) in resp.raw.headers.items() if
#                        name.lower() not in excluded_headers]
#             response = Response(resp.content, resp.status_code, headers)
#             return response
#
#     return jsonify({"error": "No running proxy found for the specified agent and box"}), 404
#
# def availableProxyPort():
#     creds = load_creds()
#     proxy_ports = creds["proxy"]["ports"]
#     allocations = creds["proxy"].get("allocation", {})
#
#     # Find used ports from running allocations
#     used_ports = set()
#     for box_id, data in allocations.items():
#         if data["status"] == "running":
#             port = int(box_id.split("_")[-1])
#             used_ports.add(port)
#
#     # Check system-used ports with netstat
#     cmd = "netstat -tuln | awk '{print $4}' | grep -E ':[0-9]+' | cut -d':' -f2"
#     result = run_command(cmd)
#     if result.startswith("[ERROR]") or result.startswith("[EXCEPTION]"):
#         logging.error(f"[Server] netstat failed: {result}")
#         system_ports = set()
#     else:
#         system_ports = {int(port) for port in result.split('\n') if port.isdigit()}
#
#     # Find available ports
#     available_ports = [port for port in proxy_ports if port not in used_ports and port not in system_ports]
#
#     if available_ports:
#         return available_ports[0]
#
#     # Reuse port from stopped container
#     for box_id, data in allocations.items():
#         if data["status"] == "stopped":
#             port = int(box_id.split("_")[-1])
#             deleteBox(box_id)
#             return port
#
#     return None

@app.route('/<api_key>/ttt', methods=['GET'])
def ttt(api_key):
    creds_data = load_creds()
    if check_api(api_key, creds_data) == "admin":
        return jsonify(ttt())
    return jsonify("Invalid API key.")

def ttt():
    return "FFFFFFFFFFFF"

def deleteBox(box_id):
    box_dir = os.path.join(os.getcwd(), "connects", box_id)
    if not os.path.isdir(box_dir):
        logging.error(f"[Server] Directory {box_dir} does not exist")
        return f"[Server] Directory {box_dir} does not exist."

    try:
        run_command(f"tmux send-keys -t {box_id} C-c")
        sleep(1)
        run_command(f"tmux kill-session -t {box_id}")
        run_command(f"rm -rf {box_dir}")
        logging.info(f"[Server] Box {box_id} deleted successfully")
        return f"[Server] Box {box_id} deleted successfully"
    except Exception as e:
        logging.error(f"[Server] Error deleting box {box_id}: {str(e)}")
        return f"[Server] Error deleting box {box_id}: {str(e)}"

def createNewBoxAgent(arg):
    box_id = arg["boxID"]
    compose = arg["compose"]
    nginx_conf = arg["nginx_conf"]
    try:
        run_command(f"cd connects; mkdir {box_id}")
        run_command(f"cd connects; cd {box_id}; echo \"{compose}\" > docker-compose.yml;")
        run_command(f"cd connects; cd {box_id}; echo \"{nginx_conf}\" > nginx.conf;")
    except Exception as e:
        return f"[EXCEPTION] {str(e)}"
    return f"Create box {box_id} successfully"

def startBox(box_id):
    box_dir = os.path.join(os.getcwd(), "connects", box_id)
    if not os.path.isdir(box_dir):
        logging.error(f"[Server] Directory {box_dir} does not exist")
        return f"[Server] Directory {box_dir} does not exist."

    try:
        run_command(f"tmux new-session -d -s {box_id} -x 100 -y 1000")
        run_command(f"tmux send-keys -t {box_id} 'cd {box_dir}; docker-compose up' C-m")
        sleep(2)
        output = run_command(f"tmux capture-pane -t {box_id} -p")
        logging.info(f"[Server] Box {box_id} started")
        return f"[Server] Box {box_id} started"
    except Exception as e:
        logging.error(f"[Server] Error starting box {box_id}: {str(e)}")
        return f"[Server] Error starting box {box_id}: {str(e)}"

def stopBox(box_id):
    try:
        run_command(f"tmux send-keys -t {box_id} C-c")
        sleep(1)
        run_command(f"tmux kill-session -t {box_id}")
        logging.info(f"[Server] Box {box_id} stopped")
        return f"[Server] Box {box_id} stopped"
    except Exception as e:
        logging.error(f"[Server] Error stopping box {box_id}: {str(e)}")
        return f"[Server] Error stopping box {box_id}: {str(e)}"

def load_creds():
    """Load creds.json with thread-safe access."""
    creds_file = "creds.json"
    lock_file = creds_file + ".lock"
    with open(lock_file, "w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            if os.path.exists(creds_file) and os.path.getsize(creds_file) > 0:
                with open(creds_file, "r") as f:
                    return json.load(f)
            return {"agents": {}, "admins": {}, "credentials": {}, "sharehost": "", "listenport": 5000}
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

def save_creds(creds):
    """Save creds.json with thread-safe access."""
    creds_file = "creds.json"
    lock_file = creds_file + ".lock"
    with open(lock_file, "w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            with open(creds_file, "w") as f:
                json.dump(creds, f, indent=4)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

def get_next_agent_id(creds):
    """Generate the next available agent ID (e.g., agent04)."""
    existing_ids = [agent_id for agent_id in creds["agents"].keys() if agent_id.startswith("agent")]
    if not existing_ids:
        return "agent01"
    max_suffix = max(int(agent_id.replace("agent", "")) for agent_id in existing_ids)
    return f"agent{max_suffix + 1:02d}"

def generate_api_key():
    """Generate a 64-character alphanumeric API key."""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(64))

@app.route('/<api_key>/agents/agentDynamic/<path:archive_name>', methods=['GET'])
def download_agent(api_key, archive_name):
    """Serve the tar.gz archive for the specified agent."""
    if check_api(api_key, load_creds()) != "admin":
        return jsonify({"error": "Invalid API key."}), 403

    archive_path = os.path.join("agents", "agentDynamic", archive_name)
    if not os.path.exists(archive_path):
        return jsonify({"error": f"Archive {archive_name} not found."}), 404

    return send_file(archive_path, as_attachment=True, download_name=archive_name)


if __name__ == '__main__':
    # Load environment variables from .env file
    load_dotenv()

    # Check for required environment variables
    required_env_vars = ['FE_LOGIN_USERNAME', 'FE_LOGIN_PASSWORD', 'SHAREHOST', 'LISTEN_PORT', 'FE_API']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)

    # Get environment variables
    username = os.getenv('FE_LOGIN_USERNAME')
    password = os.getenv('FE_LOGIN_PASSWORD')
    sharehost = os.getenv('SHAREHOST')
    listen_port = os.getenv('LISTEN_PORT')
    api_key = os.getenv('FE_API')

    # Validate listen port
    try:
        listen_port = int(listen_port)
        if not (1 <= listen_port <= 65535):
            raise ValueError
    except ValueError:
        print("Error: LISTEN_PORT must be a valid port number (1-65535)")
        exit(1)

    # Load existing credentials
    creds = load_creds()

    # Update credentials with hashed password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    creds['credentials'][username] = {"password": f"{hashed_password}"}

    # Update admins with API key for Administrator
    creds['admins']['Administrator'] = api_key

    # Update sharehost and listen port
    creds['sharehost'] = sharehost
    creds['listenport'] = listen_port

    # Save updated credentials
    save_creds(creds)

    # Start Flask app
    print(f"Starting server on {sharehost}:{listen_port}")
    app.run(host="0.0.0.0", port=listen_port)