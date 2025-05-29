import argparse
import os
import re
from pathlib import Path
import time
import random
import string
import subprocess
from time import sleep
import requests

url="http://192.168.32.130:5555/JZU1a4iArzK81nxuqCaGjpkCnS6lQrpdPxBIEYyeAT8VUHCfnBhPs3ZgTvK784pL/"
ServerUrl = "localhost"

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
    f = open("RenderFormula.txt", "r")
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

def list_available_services():
    DOCKER_REFERENCE_PATH=run_command("pwd")+"/DockerFilesReference"
    services = [
        name for name in os.listdir(DOCKER_REFERENCE_PATH)
        if os.path.isdir(os.path.join(DOCKER_REFERENCE_PATH, name))
    ]
    return services

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

    thisPath=run_command("pwd")
    service = list_available_services()

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
    run_command("cd Box; mkdir " + ThisBox + "_" + arg)
    targetPath=thisPath+"/DockerFilesReference/"+arg+"/docker-compose.yml"
    print(targetPath)
    f = open(targetPath, "r")
    st = ""
    for i in f:
        st += i
    compose=render(st,variableGen(extract_variables_from_compose(targetPath)))
    composepath=thisPath+"/box/"+ThisBox+"_"+arg+"/docker-compose.yml"
    o=open(composepath,"w")
    o.write(compose)
    return

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

def add_task(agent_id, command):
    url = f"http://"+ServerUrl+":5000/addTask/"+agent_id
    payload = {"command": command}

    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def add_tasks(agent_id, commands : list):
    ans = []
    for i in commands:
        ans.append(add_task(agent_id,i))
    return ans

def get_task_queue(agent_id):
    url = f"http://"+ServerUrl+":5000/getTask/"+agent_id
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_output(agent_id):
    url = f"http://"+ServerUrl+":5000/getReport/"+agent_id
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def stats(arg):
    return

def loop():
    while(True):
        sleep(1)

def serviceStats(arg):
    return

def agentStats(arg):
    print(arg)
    add_task(arg,"cat /etc/os-release")
    return(get_output(arg).get("reports")[-1].get("output"))

def agentList():
    url = f"http://" + ServerUrl + ":5000/getAgents"
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def addNewAgent(arg):
    url = f"http://" + ServerUrl + ":5000/register/" + arg
    try:
        response = requests.post(url)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def test():
    print(get_output("agent01"))

def main():

    parser = argparse.ArgumentParser(description="CloudBox CLI modular tool")

    # Add flags/arguments
    # parser.add_argument("--nmapFull", type=str, help=" --nmapFUll [IP]")
    # parser.add_argument("--readNmap", action="store_true", help="Return Nmap result of closest scan")

    parser.add_argument("--extractVariables", type=str, help="path to docker-compose")
    parser.add_argument("--genBoxID", action="store_true", help="Generate timestamp random ID")
    parser.add_argument("--listAvailableServices", action="store_true", help="List available service templates")
    parser.add_argument("--TestFunction", action="store_true", help="Use for testing")

    parser.add_argument("--addTask", nargs="?", const="default", help="Create new service")
    parser.add_argument("--getOutput", nargs="?", const="default", help="Create new service")
    # parser.add_argument("--createNewBoxAutomate", nargs="?", const="default", help="Create new service")

    parser.add_argument("--createNewBoxAutomate", nargs="?", const="default", help="Create new service")
    parser.add_argument("--servicesStats", nargs="?", const="default", help="Check services status")
    parser.add_argument("--agentStats", nargs="?", const="default", help="Check Agents status")
    parser.add_argument("--addNewAgent", nargs="?", const="default", help="Create new service")


    args = parser.parse_args()

    if args.extractVariables:
        variable = extract_variables_from_compose(args.extractVariables)
        print(variable)

    if args.genBoxID:
        print(generate_box_id(10))

    if args.createNewBoxAutomate:
        createNewBox(args.createNewBoxAutomate)

    if args.listAvailableServices:
        service = list_available_services()
        print(service)

    if args.servicesStats:
        serviceStats(args.servicesStats)

    if args.agentStats:
        print(agentStats(args.agentStats))

    if args.addNewAgent:
        addNewAgent(args.addNewAgent)

    if args.TestFunction:
        test()

    if args.addTask:
        print(add_task(args.addTask.split(",")[0],args.addTask.split(",")[1]))

    if args.getOutput:
        try:
            if(args.getOutput.split(",")[1]=="n"):
                print(get_output(args.getOutput.split(",")[0]).get("reports")[-1].get("output"))
        except:
            print(get_output(args.getOutput))

    # if args.nmapFull:
    #     nmapFullScan(args.nmapFull)
    #
    # if args.readNmap:
    #     print(readNmap())

if __name__ == '__main__':
    main()
