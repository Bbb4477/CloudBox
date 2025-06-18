import json

from flask import jsonify

s = "{\"BlockIO\":\"184MB / 37.9MB\",\"CPUPerc\":\"40.23%\",\"Container\":\"a683fd92d20d\",\"ID\":\"a683fd92d20d\",\"MemPerc\":\"1.37%\",\"MemUsage\":\"26.34MiB / 1.882GiB\",\"Name\":\"1749122872_exrusaott9_wordpress_wordpress_1\",\"NetIO\":\"586B / 126B\",\"PIDs\":\"3\"}\n{\"BlockIO\":\"101MB / 153MB\",\"CPUPerc\":\"40.59%\",\"Container\":\"08a20e960da1\",\"ID\":\"08a20e960da1\",\"MemPerc\":\"5.93%\",\"MemUsage\":\"114.3MiB / 1.882GiB\",\"Name\":\"1749122872_exrusaott9_wordpress_db_1\",\"NetIO\":\"1.24kB / 126B\",\"PIDs\":\"22\"}\n{\"BlockIO\":\"44.1MB / 229kB\",\"CPUPerc\":\"1.59%\",\"Container\":\"1cedc7d5afed\",\"ID\":\"1cedc7d5afed\",\"MemPerc\":\"0.52%\",\"MemUsage\":\"10MiB / 1.882GiB\",\"Name\":\"1749122878_qtsxgi1zbw_filebrowser_filebrowser_1\",\"NetIO\":\"1.32kB / 126B\",\"PIDs\":\"5\"}"

decoded_str = s.encode().decode('unicode_escape')

# Step 2: Split into individual JSON strings
json_strings = decoded_str.strip().split('\n')

# Step 3: Parse and restructure
result = {}
for item in json_strings:
    obj = json.loads(item)
    name = obj.get("Name")
    if name:
        result[name] = obj

# Optional: Pretty print the result
print(json.dumps(result, indent=2))

