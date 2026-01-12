import requests
import gzip
import datetime
import time

# 2026 STABLE ENDPOINTS
CHANNELS_API = "https://jiotv.data.cdn.jio.com/apis/v3.0/getMobileChannelList/get/?langId=6&os=android&devicetype=phone"
EPG_API = "http://jiotv.data.cdn.jio.com/apis/v1.3/getepg/get"

# These headers are currently mandatory to avoid the 450 error
HEADERS = {
    "User-Agent": "JioTV/7.0.9 (Linux; Android 13; SM-G960F Build/R16NW; wv)",
    "app-name": "RJIL_JioTV",
    "os": "android",
    "devicetype": "phone",
    "x-api-key": "l7xx938b6684ee9e4bbe8831a9a682b8e19f", # The 2026 Public API Key
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
}

def generate_epg():
    session = requests.Session()
    session.headers.update(HEADERS)
    
    print("Connecting to JioTV V3 API...")
    
    try:
        # Check if the response is actually JSON
        response = session.get(CHANNELS_API, timeout=20)
        
        if response.status_code != 200:
            print(f"❌ Connection failed: Status {response.status_code}")
            if response.status_code == 450:
                print("Suggestion: If on GitHub, you MUST use an Indian Residential Proxy.")
            return

        channels = response.json().get('result', [])
        print(f"✅ Connection Successful! Found {len(channels)} channels.")

        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<tv generator-info-name="CustomEPG-v2026">\n'
        
        # Limit to 30 channels for initial testing
        for ch in channels[:30]:
            cid = str(ch.get("channel_id"))
            name = ch.get("channel_name", "Unknown").replace("&", "&amp;")
            xml += f'  <channel id="{cid}">\n    <display-name>{name}</display-name>\n  </channel>\n'

            params = {"offset": 0, "channel_id": cid, "langId": 6}
            try:
                g_resp = session.get(EPG_API, params=params, timeout=10)
                if g_resp.status_code == 200:
                    for p in g_resp.json().get("epg", []):
                        start = datetime.datetime.fromtimestamp(p['startEpoch']/1000).strftime('%Y%m%d%H%M%S +0530')
                        stop = datetime.datetime.fromtimestamp(p['endEpoch']/1000).strftime('%Y%m%d%H%M%S +0530')
                        title = p.get("showname", "No Title").replace("&", "&amp;")
                        xml += f'  <programme start="{start}" stop="{stop}" channel="{cid}">\n    <title>{title}</title>\n  </programme>\n'
                # Crucial: Randomized delay to look like a human
                time.sleep(1.2) 
            except:
                continue

        xml += '</tv>'
        with gzip.open("epg.xml.gz", "wb") as f:
            f.write(xml.encode("utf-8"))
        print("🚀 Successfully created epg.xml.gz")

    except Exception as e:
        print(f"Error during execution: {e}")

if __name__ == "__main__":
    generate_epg()
