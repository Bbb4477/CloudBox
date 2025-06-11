
from flask import Flask, jsonify, request
from threading import Lock
import json
import socket
import os
import argparse
import re
from pathlib import Path
import time
import random
import string
import subprocess
from time import sleep
import requests
import base64
import struct
from flask_cors import CORS


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

def render(source, boxVariables : list):
    rendered = source

    # Convert list of lists into a dictionary for easier replacement
    var_dict = {k: v for k, v in boxVariables}

    # Replace all {Variable} patterns with their corresponding values
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
            s.settimeout(2)
            s.connect((address, port))
            return True
    except (ConnectionRefusedError, socket.timeout, OSError, ValueError):
        return False


def check_api(api,creds):
    if api in creds['admins'].values():
        return "admin"

        # Check in agents
    for agent in creds['agents'].values():
        if agent['API'] == api:
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
    ans=[]
    for i in creds["agents"]:
        ans.append(i)
    return ans

@app.route('/<api_key>/agent/box/list', methods=['POST'])
def boxListAPI(api_key):
    if check_api(api_key, creds) == "admin":
        data = request.get_json()
        if not data or "agentID" not in data:
            return jsonify({"error": "Missing agentID in JSON body"}), 400
        agentID = data["agentID"]
        if find(listAgent(), agentID) == -1:
            return jsonify("Invalid AgentID")
        return jsonify(boxList(agentID))
    return jsonify("Invalid API key.")

def boxList(agentID):
    payload = creds["agents"][agentID]["API"] + " box_status"
    result = socketSend(creds["agents"][agentID]["host"], payload)
    if result.startswith("Connection error:"):
        return result  # Return error string (e.g., "Connection error: 192.168.32.132:5000 is disconnected or stopped")
    return result.split(' ')
    # try:
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #         s.connect((creds["agents"][agentID]["ip"], creds["agents"][agentID]["port"]))
    #         payload = creds["agents"][agentID]["API"]+" box_status"
    #         s.sendall(payload.encode())
    #         output = s.recv(4096).decode()
    #     return output.split(' ')
    # except Exception as e:
    #     return e


@app.route('/<api_key>/agent/box/stats', methods=['POST'])
def boxStatus(api_key):
    return

def boxStatus(agentID,boxID):
    return

@app.route('/<api_key>/agent/box/start', methods=['POST'])
def boxStartAPI(api_key):
    if check_api(api_key, creds) == "admin":
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
    secret = creds["agents"][agentID]["API"]
    payload = f"{secret} box_start {boxID}"
    return socketSend(creds["agents"][agentID]["host"], payload)

@app.route('/<api_key>/agent/box/stop', methods=['POST'])
def boxStopAPI(api_key):
    if check_api(api_key, creds) == "admin":
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
    secret = creds["agents"][agentID]["API"]
    payload = f"{secret} box_stop {boxID}"
    return socketSend(creds["agents"][agentID]["host"], payload)

@app.route('/<api_key>/agent/box/delete', methods=['POST'])
def boxDeleteAPI(api_key):
    if check_api(api_key, creds) == "admin":
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
    secret = creds["agents"][agentID]["API"]
    payload = f"{secret} box_delete {boxID}"
    return socketSend(creds["agents"][agentID]["host"], payload)

@app.route('/<api_key>/agent/status', methods=['POST'])
def agentStatusAPI(api_key):
    return

def agentStatus(agentID):
    return

@app.route('/<api_key>/agent/inspect', methods=['POST'])
def inspectAgent(api_key ):
    data = request.get_json()
    if not data or "agentID" not in data:
        return jsonify({"error": "Missing agentID in JSON body"}), 400
    agentID = data["agentID"]
    if check_api(api_key, creds) == "admin":
        if(find(listAgent(),agentID)!=-1):
            return creds["agents"][agentID]
        return jsonify("Invalid AgentID")
    return jsonify("Invalid API key.")

@app.route('/<api_key>/server/availableService', methods=['POST'])
def listServices(api_key):
    if check_api(api_key, creds) == "admin":
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
    if check_api(api_key, creds) == "admin":
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
    if find(listAgent(), agentID) == -1:
        return "Error, no Agent available"
    if find(list_available_services(), service) == -1:
        return f"No {service} currently available in template stores"
    payload = createNewBoxNoDirectCommand(service)
    return send_command_LoopUntilFinish(creds["agents"][agentID]["host"], payload, creds["agents"][agentID]["API"])

@app.route('/<api_key>/agent/overview', methods=['POST'])
def AgentOverview(api_key):
    if check_api(api_key, creds) == "admin":
        data = request.get_json()
        if not data or "agentID" not in data:
            return jsonify({"error": "Missing agentID in JSON body"}), 400
        agentID = data["agentID"]
        if find(listAgent(), agentID) == -1:
            return jsonify("Invalid AgentID")
        return jsonify(AgentOverview(agentID))
    return jsonify("Invalid API key.")

def AgentOverview(agentID):
    secret = creds["agents"][agentID]["API"]
    payload = f"{secret} agent_stats"
    return socketSend(creds["agents"][agentID]["host"], payload)

@app.route('/<api_key>/ttt', methods=['GET'])
def ttt(api_key):
    if check_api(api_key, creds) == "admin":
        return jsonify(ttt())
    return jsonify("Invalid API key.")

def ttt():
    return "FFFFFFFFFFFF"



if __name__ == '__main__':
    f = open("creds.json", "r")
    creds = json.load(f)
    app.run(host="0.0.0.0", port=5000)
    # print(check_agent_status(creds["agents"]["agent01"]["host"]))