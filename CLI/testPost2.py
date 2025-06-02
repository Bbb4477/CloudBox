import requests
import json
import socket

# JSON payload

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("192.168.32.133", 5000))
    # Prepend secret path
    # payload = f"JZU1a4iArzK81nxuqCaGjpkCnS6lQrpdPxBIEYyeAT8VUHCfnBhPs3ZgTvK784pL box_status"
    # payload = f"JZU1a4iArzK81nxuqCaGjpkCnS6lQrpdPxBIEYyeAT8VUHCfnBhPs3ZgTvK784pL box_start 1748857954_O9mUTockug_wordpress"
    # payload = f"JZU1a4iArzK81nxuqCaGjpkCnS6lQrpdPxBIEYyeAT8VUHCfnBhPs3ZgTvK784pL box_stop 1748857954_O9mUTockug_wordpress"
    # payload = f"SpecialExecutionJZU1a4iArzK81nxuqCaGjpkCnS6lQrpdPxBIEYyeAT8VUHCfnBhPs3ZgTvK784pL box_inspect 1748534111_8Hbj6rlsNn_wordpress"
    # print(payload)

    s.sendall(payload.encode())
    output = s.recv(4096).decode()
    print(output)

