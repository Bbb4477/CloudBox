import requests

api_key = "joQitzSI4jenCsIbJ1cLfw4uDgIBeayztKer41HH4jr1QDTXQYivOqcqYAk3I3c7"
endpoint = "box/availableService"

url = f'http://192.168.32.130:5000/{api_key}/{endpoint}'

response = requests.get(url)
print("Status:", response.status_code)
print("Response:", response.json())