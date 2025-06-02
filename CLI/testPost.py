import requests
import json

# Change this to your API server URL
api_server = "http://192.168.32.130:5000"
api_key = "joQitzSI4jenCsIbJ1cLfw4uDgIBeayztKer41HH4jr1QDTXQYivOqcqYAk3I3c7"

url = f"{api_server}/{api_key}/agent/box/stop"

# JSON payload
payload = {
    "agentID": "agent02",
    "boxID": "1748857954_O9mUTockug_wordpress"
}

# payload = {
#     "agentID": "agent02",
#     "service": "wordpress"
# }

# Send the POST request with JSON data
response = requests.post(url, json=payload)

# Print the response from the server
print("Status Code:", response.status_code)
print("Response JSON:", response.json())