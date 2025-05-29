# server_push_with_api_key.py
import json
import socket

def send_command(agent_ip, agent_port, command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((agent_ip, agent_port))
        # Prepend secret path
        payload = f"{SECRET_PATH} {command}"
        s.sendall(payload.encode())
        output = s.recv(4096).decode()
        return output

f = open("agentConfig.json","r")
o = json.load(f)
SECRET_PATH = o['API']
# Example usage
agent_ip = "192.168.32.132"
agent_port = 5000
command = "whoami"

result = send_command(agent_ip, agent_port, command)
print(f"[Server] Output:\n{result}")
