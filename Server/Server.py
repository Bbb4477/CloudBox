# server.py
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

app = Flask(__name__)


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
        print("Services available: ", end="")
        for i in service:
            print(i, end=" ")
        print()
        while (True):
            inp = input("Input your service pick: ")
            if find(service, inp) != -1:
                break
            if (inp == ""):
                return
            print("service not found")
        arg = inp

    elif find(service, arg) == -1:
        print("Service not found")
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

def find_available_ports(lower: int, upper: int, count: int = 1) -> list:
    used_ports = set()

    # Run netstat to get list of used ports
    output = run_command("netstat -tuln")
    print(output)

    # Extract all numeric ports from the output
    matches = re.findall(r':(\d+)', output)
    for port in matches:
        used_ports.add(int(port))
    print(used_ports)
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
        print(payload)
        s.sendall(payload.encode())
        output = s.recv(4096).decode()
        return output

def ApplyBox(service, agentID):
    if find(listAgent(),agentID) == -1:
        return ["Error, no Agent available"]
    if find(list_available_services(),service) == -1:
        return [f"No {service} currently available in template stores"]
    cc = createNewBox(service)
    ans = []
    print(ans)
    for i in cc["commands"]:
        print(i)
        ans.append(send_command(creds["agents"][agentID]["ip"], 5000, i, creds["agents"][agentID]["API"]))
    return ans

def check_api(api,creds):
    if api in creds['admins'].values():
        return "admin"

        # Check in agents
    for agent in creds['agents'].values():
        if agent['API'] == api:
            return "agent"

    return None

@app.route('/<api_key>/agent/list', methods=['GET'])
def listAgent(api_key):
    if check_api(api_key,creds)=="admin":
        ans = creds["agents"]
        for i in ans:
            ans[i]["API"]="********"
        return ans
    return jsonify("Invalid API key.")

def listAgent() -> list:
    ans=[]
    for i in creds["agents"]:
        ans.append(i)
    return ans

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

@app.route('/<api_key>/box/availableService', methods=['GET'])
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

@app.route('/<api_key>/box/install', methods=['POST'])
def ApplyBoxAPI(api_key):
    if check_api(api_key, creds) == "admin":
        data = request.get_json()
        # if not data or "agentID" or "service" not in data:
        #     return jsonify({"error": "Missing agentID in JSON body"}), 400
        agentID = data["agentID"]
        service = data["service"]
        return jsonify(ApplyBox(service, agentID))
    return jsonify("Invalid API key.")

# @app.route('/<api_key>/agent/list', methods=['POST'])
# def listAgent(api_key):
#     if check_api(api_key,creds)=="admin":
#         ans = creds["agents"]
#         return ans
#     return jsonify("Invalid API key.")


if __name__ == '__main__':
    f = open("creds.json", "r")
    creds = json.load(f)
    # print(listAgent())
    # print(list_available_services())
    # print(ApplyBox("prestashop","agent02"))
    app.run(host="0.0.0.0", port=5000)

# Preset commands per agent

# Storage for received outputs

# @app.route('/agent/add/<agent_id>', methods=['POST'])
# def add_Agent(agent_id):
#     return
#
# @app.route('/agent/sync', methods=['GET'])
# def add_Agent(agent_id):
#     return
#
# @app.route('/get/<agent_id>', methods=['GET'])
# def get_command(agent_id):
#     return
#
# @app.route('/addTask/<agent_id>', methods=['POST'])
# def add_command_queue(agent_id):
#     return

# @app.route(f"/{API_KEY}/agent/add/<agent_id>", methods=['POST'])
# def add_Agent(agent_id,api):
#     return