# agent_listener_with_api_key.py
import socket
import subprocess
import json

HOST = '0.0.0.0'
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
                print(f"[Agent] Raw data: {data}")

                # Check if the data starts with the secret path
                if data.startswith(SECRET_PATH):
                    # Remove the secret path part
                    command = data[len(SECRET_PATH):].strip()
                    if command.__contains__(f"SpecialExecution{SECRET_PATH}"):
                        return "SSS"
                    print(f"[Agent] Valid command received: {command}")
                    try:
                        output = subprocess.check_output(command, shell=True, text=True)
                        conn.sendall(output.encode())
                    except Exception as e:
                        conn.sendall(str(e).encode())
                else:
                    print("[Agent] Invalid API key/path. Ignored.")
                    conn.sendall(b"Invalid API key/path.")

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
    start_agent_listener()
