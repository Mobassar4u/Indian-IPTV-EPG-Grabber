import requests
import json
import datetime
import os
import random

# --- CONFIGURATION ---
# Spoof an Indian IP address to bypass basic geo-fencing
INDIAN_IPS = [
    "49.36.0.0", "103.25.172.0", "157.32.0.0", "106.192.0.0", "1.38.0.0"
]
SPOOFED_IP = random.choice(INDIAN_IPS)

HEADERS = {
    "User-Agent": "JioTV 7.0.5 (Android 10)",
    "appkey": "NzNiMDhlYzQyNjJm",
    "devicetype": "phone",
    "os": "android",
    "versionCode": "300",
    "X-Forwarded-For": SPOOFED_IP,  # Spoofs Indian location
    "X-Real-IP": SPOOFED_IP,
    "Accept": "application/json"
}

# Optional: Add public Indian proxies if XFF headers are blocked
PROXIES = {
    # "http": "http://username:password@indian-proxy-ip:port",
    # "https": "http://username:password@indian-proxy-ip:port"
}

def get_channels():
    # Use the v1.3 endpoint which is currently more stable
    url = "https://jiotv.data.cdn.jio.com/apis/v1.3/getMobileChannelList/get/?os=android&devicetype=phone&version=300"
    try:
        # Pass proxies=PROXIES if using a proxy service
        response = requests.get(url, headers=HEADERS, proxies=PROXIES, timeout=15)
        if response.status_code == 200:
            channels = response.json().get("result", [])
            print(f"Successfully fetched {len(channels)} channels.")
            return channels
        else:
            print(f"Blocked with Status: {response.status_code}. Try an Indian Proxy.")
    except Exception as e:
        print(f"Network Error: {e}")
    return []

def write_xml(channels):
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n')
        for c in channels:
            cid = c.get("channel_id")
            name = str(c.get("channel_name", "")).replace("&", "&amp;")
            logo = c.get("logoUrl", "")
            f.write(f'  <channel id="{cid}">\n    <display-name>{name}</display-name>\n')
            f.write(f'    <icon src="{logo}" />\n  </channel>\n')
        f.write('</tv>')

if __name__ == "__main__":
    channel_list = get_channels()
    if channel_list:
        write_xml(channel_list)
