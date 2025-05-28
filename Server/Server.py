# server.py
from flask import Flask, jsonify, request
from threading import Lock

app = Flask(__name__)

# Preset commands per agent
agent_commands = {
    "agent01": ["pwd", "ifconfig", "whoami"],
    "agent02": ["whoami", "uptime"]
}

# Storage for received outputs
agent_results = {}

lock = Lock()

@app.route('/get/<agent_id>', methods=['GET'])
def get_command(agent_id):
    with lock:
        if agent_id not in agent_commands or not agent_commands[agent_id]:
            return jsonify({"command": None})
        cmd = agent_commands[agent_id].pop(0)
        return jsonify({"command": cmd})

@app.route('/getTask/<agent_id>', methods=['GET'])
def get_commands(agent_id):
    with lock:
        if agent_id not in agent_commands or not agent_commands[agent_id]:
            return jsonify({"command": None})
        cmd = agent_commands[agent_id]
        return jsonify({agent_id: cmd})

@app.route('/addTask/<agent_id>', methods=['POST'])
def add_command_queue(agent_id):
    data = request.json
    command = data.get("command")

    if not command:
        return jsonify({"error": "No command provided"}), 400

    if agent_id not in agent_commands:
        return jsonify({"error": "Agent not found"}), 404

    agent_commands[agent_id].append(command)
    return jsonify({"message": f"Command added to {agent_id}'s queue"}), 200

@app.route('/register/<agent_id>', methods=['POST'])
def add_agent(agent_id):
    if agent_id not in agent_commands:
        agent_commands[agent_id] = []  # Initialize empty command queue
        return jsonify({"message": f"Agent '{agent_id}' registered successfully."}), 201
    else:
        return jsonify({"message": f"Agent '{agent_id}' is already registered."}), 200

@app.route('/report/<agent_id>', methods=['POST'])
def receive_output(agent_id):
    data = request.get_json()
    cmd = data.get("command")
    output = data.get("output")
    with lock:
        if agent_id not in agent_results:
            agent_results[agent_id] = []
        agent_results[agent_id].append({"command": cmd, "output": output})
    print(f"[Server] Output from {agent_id} - {cmd}:\n{output}")
    return jsonify({"status": "received"})

@app.route('/getReport/<agent_id>', methods=['GET'])
def get_report(agent_id):
    with lock:
        results = agent_results.get(agent_id, [])
    return jsonify({"agent_id": agent_id, "reports": results}), 200

@app.route('/getAgents', methods=['GET'])
def get_agents():
    return jsonify({"agents": list(agent_commands.keys())}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

