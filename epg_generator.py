import requests
import gzip
import datetime
import time
import sys

# Constants
CHANNELS_API = "https://jiotv.data.cdn.jio.com/apis/v3.0/getMobileChannelList/get/?langId=6&os=android&devicetype=phone"
EPG_API = "http://jiotv.data.cdn.jio.com/apis/v1.3/getepg/get"

# Enhanced Headers to mimic the latest Android app
HEADERS = {
    "User-Agent": "JioTV/7.0.9 (Linux; Android 13; SM-S908E Build/TP1A.220624.014; wv)",
    "app-name": "RJIL_JioTV",
    "os": "android",
    "devicetype": "phone",
    "x-apisign-v2": "308010534224", # Static sign often used in v3
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
}

def generate_epg():
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # --- IF RUNNING ON GITHUB ACTIONS, UNCOMMENT AND ADD PROXY ---
    # session.proxies = {
    #     "http": "http://your_indian_proxy:port",
    #     "https": "http://your_indian_proxy:port"
    # }

    try:
        print("Connecting to JioTV...")
        response = session.get(CHANNELS_API, timeout=25)
        
        if response.status_code == 450:
            print("❌ Error 450: Still Blocked. Reason: Non-Indian IP or Flagged Headers.")
            return

        channels = response.json().get('result', [])
        print(f"✅ Success! Processing {len(channels[:50])} channels...")

        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<tv generator-info-name="JioEPG-Bypass">\n'
        
        for ch in channels[:50]:
            cid, name = str(ch.get("channel_id")), ch.get("channel_name", "Unknown").replace("&", "&amp;")
            xml += f'  <channel id="{cid}">\n    <display-name>{name}</display-name>\n  </channel>\n'

            # Fetch EPG with a slight randomized delay to look human
            params = {"offset": 0, "channel_id": cid, "langId": 6}
            try:
                guide_resp = session.get(EPG_API, params=params, timeout=10)
                if guide_resp.status_code == 200:
                    for p in guide_resp.json().get("epg", []):
                        start = datetime.datetime.fromtimestamp(p['startEpoch']/1000).strftime('%Y%m%d%H%M%S +0530')
                        stop = datetime.datetime.fromtimestamp(p['endEpoch']/1000).strftime('%Y%m%d%H%M%S +0530')
                        title = p.get("showname", "No Title").replace("&", "&amp;")
                        xml += f'  <programme start="{start}" stop="{stop}" channel="{cid}">\n    <title>{title}</title>\n  </programme>\n'
                time.sleep(0.5) 
            except:
                continue

        xml += '</tv>'
        with gzip.open("epg.xml.gz", "wb") as f:
            f.write(xml.encode("utf-8"))
        print("🚀 File 'epg.xml.gz' created.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    generate_epg()
