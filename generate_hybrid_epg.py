import requests, json
from datetime import datetime, timedelta
from lxml import etree
import pytz

TZ = pytz.timezone("Asia/Kolkata")

with open("channels.json") as f:
    channels = json.load(f)

root = etree.Element("tv")

# Channel nodes
for ch in channels:
    c = etree.SubElement(root,"channel",id=ch["id"])
    etree.SubElement(c,"display-name").text = ch["name"]
    etree.SubElement(c,"icon",src=ch["logo"])

# Tata Play feed
def tata_epg(cid, date):
    url = f"https://tm.tapi.tatasky.com/tata-sky-epg/v3/epg/channel/{cid}/date/{date}"
    r = requests.get(url,timeout=10)
    if r.status_code != 200:
        return []
    return r.json().get("programmes",[])

# JioTV feed
def jio_epg(cid):
    url = f"https://jiotvapi.media.jio.com/apis/v1.4/getepg/get?channel_id={cid}"
    r = requests.get(url,timeout=10)
    if r.status_code != 200:
        return []
    return r.json().get("epg",[])

today = datetime.now(TZ)

for ch in channels:
    # 7 days Tata Play
    for i in range(7):
        date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        for p in tata_epg(ch["tata_id"], date):
            s = datetime.fromtimestamp(p["startTime"]/1000, TZ)
            e = datetime.fromtimestamp(p["endTime"]/1000, TZ)

            pr = etree.SubElement(root,"programme",
                channel=ch["id"],
                start=s.strftime("%Y%m%d%H%M%S %z"),
                stop=e.strftime("%Y%m%d%H%M%S %z")
            )
            etree.SubElement(pr,"title").text = p["title"]
            etree.SubElement(pr,"desc").text = p.get("description","")

    # JioTV fallback (today)
    for p in jio_epg(ch["jio_id"]):
        s = datetime.fromtimestamp(int(p["start_time"]), TZ)
        e = datetime.fromtimestamp(int(p["end_time"]), TZ)
        pr = etree.SubElement(root,"programme",
            channel=ch["id"],
            start=s.strftime("%Y%m%d%H%M%S %z"),
            stop=e.strftime("%Y%m%d%H%M%S %z")
        )
        etree.SubElement(pr,"title").text = p["showname"]
        etree.SubElement(pr,"desc").text = p.get("description","")

etree.ElementTree(root).write("epg.xml",pretty_print=True,xml_declaration=True,encoding="UTF-8")
print("Hybrid EPG generated")
