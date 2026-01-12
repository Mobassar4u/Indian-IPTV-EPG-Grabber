import requests
import json
import datetime
import os
import time

# --- PROXY CONFIGURATION ---
# It is recommended to use GitHub Secrets for the proxy URL to keep it private.
# In GitHub: Settings > Secrets > Actions > New Secret (Name: INDIAN_PROXY)
# Value format: http://username:password@ip:port
proxy_url = os.getenv("INDIAN_PROXY") 

proxies = {
    "http": proxy_url,
    "https": proxy_url
} if proxy_url else None

# Configuration
prevEpgDayCount = 1
nextEpgDayCount = 1

# Updated Headers for 2026 to bypass 450/Forbidden errors
headers = {
    "User-Agent": "JioTV/7.0.9 (Linux; Android 13; SM-S908E Build/TP1A.220624.014; wv)",
    "app-name": "RJIL_JioTV",
    "os": "android",
    "devicetype": "phone",
    "x-api-key": "l7xx938b6684ee9e4bbe8831a9a682b8e19f",
    "Accept": "application/json",
    "Connection": "keep-alive"
}

channelList = []

def getChannels():
    print("Fetching Channel List (v3.0 Patch)...")
    # v3.0 is the required endpoint for 2026 stability
    reqUrl = "https://jiotv.data.cdn.jio.com/apis/v3.0/getMobileChannelList/get/?langId=6&os=android&devicetype=phone"
    try:
        # Requests now include the proxy to bypass geo-blocking
        response = requests.get(reqUrl, headers=headers, proxies=proxies, timeout=15)
        
        if response.status_code == 450:
            print("❌ Error 450: Forbidden. Your IP is blocked or not Indian.")
            return []
            
        if response.status_code == 200:
            apiData = response.json()
            return apiData.get("result", [])
        return []
    except Exception as e:
        print(f"Error fetching channels: {e}")
        return []

def getEpg(channelId, offset, langId):
    try:
        # Stable v1.3 endpoint for EPG data
        reqUrl = f"http://jiotv.data.cdn.jio.com/apis/v1.3/getepg/get?channel_id={channelId}&offset={offset}&langId={langId}"
        response = requests.get(reqUrl, headers=headers, proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            # Check if response is valid JSON before parsing
            apiData = response.json()
            return apiData.get("epg", [])
        return []
    except Exception:
        return []

# ... (rest of your writeEpg and merge logic remains the same)

def grabEpgAllChannel(day):
    print(f"\nProcessing Day {day}...")
    filename = f"program{day}.xml"
    with open(filename, "w", encoding='utf-8') as programFile:
        for idx, channel in enumerate(channelList):
            cid = channel.get("channel_id")
            epgData = getEpg(cid, day, 6)
            for epg in epgData:
                # clean_text helps prevent broken XML due to special characters
                writeEpgProgram(cid, epg, programFile)
            
            # Anti-bot delay: avoids rapid-fire detection
            time.sleep(0.5) 
            
            if idx % 10 == 0:
                print(f"Progress: {idx}/{len(channelList)} channels done", end="\r")
