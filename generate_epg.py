import requests
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time
import gzip
import os

# 1. BROWSER HEADERS
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Referer': 'https://www.tataplay.com/web-guide',
    'Accept': 'application/json, text/plain, */*'
}

def format_xml_time(ts):
    dt = datetime.datetime.fromtimestamp(int(ts)/1000)
    return dt.strftime("%Y%m%d%H%M%S +0530")

def load_channels_from_xml(filename):
    channels = []
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        for channel in root.findall('channel'):
            channels.append({
                "id": channel.get('site_id'),
                "name": channel.text.strip(),
                "xmlid": channel.get('xmltv_id')
            })
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return channels

def fetch_epg():
    channels = load_channels_from_xml("indian_channels.xml")
    if not channels:
        print("No channels found to process.")
        return

    root = ET.Element("tv", {"generator-info-name": "Indian-EPG-Generator"})
    
    # Add Channel Headers
    for ch in channels:
        c_tag = ET.SubElement(root, "channel", id=ch['xmlid'])
        ET.SubElement(c_tag, "display-name").text = ch['name']

    # 7-Day Catchup Loop
    for day_offset in range(-7, 1):
        target_date = (datetime.datetime.now() + datetime.timedelta(days=day_offset)).strftime("%d-%m-%Y")
        print(f"--- Processing {target_date} ---")

        for ch in channels:
            url = f"https://www.tataplay.com/web-guide/api/v1/channels/{ch['id']}/schedule?date={target_date}"
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    programs = data.get('data', {}).get('schedules', [])
                    for prog in programs:
                        p_tag = ET.SubElement(root, "programme", 
                                             start=format_xml_time(prog['startTime']), 
                                             stop=format_xml_time(prog['endTime']), 
                                             channel=ch['xmlid'])
                        ET.SubElement(p_tag, "title", lang="hi").text = prog.get('title', 'Unknown')
                        ET.SubElement(p_tag, "desc", lang="hi").text = prog.get('description', 'No info')
                else:
                    print(f"Skipping {ch['name']} (ID: {ch['id']}): HTTP {response.status_code}")
                time.sleep(0.5) 
            except Exception as e:
                print(f"Failed {ch['name']}: {e}")

    # Save XML
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)
    
    # Compress
    with open("epg.xml", "rb") as f_in, gzip.open("epg.xml.gz", "wb") as f_out:
        f_out.writelines(f_in)
    print("Success: epg.xml.gz generated.")

if __name__ == "__main__":
    fetch_epg()
