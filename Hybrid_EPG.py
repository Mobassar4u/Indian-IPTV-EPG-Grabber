import json
import requests
from datetime import datetime, timedelta
from lxml import etree
import pytz
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------- CONFIG ----------------
TZ = pytz.timezone("Asia/Kolkata")
DAYS = 7
TIMEOUT = 20

# --------------- SESSION ----------------
session = requests.Session()

retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Accept": "application/json",
    "Connection": "close"
}

# --------------- LOAD CHANNELS ----------
with open("channels.json", "r", encoding="utf-8") as f:
    channels = json.load(f)

# --------------- XML ROOT ----------------
root = etree.Element("tv")

for ch in channels:
    c = etree.SubElement(root, "channel", id=ch["id"])
    etree.SubElement(c, "display-name").text = ch["name"]
    etree.SubElement(c, "icon", src=ch["logo"])

# --------------- TATA PLAY EPG ----------
def tata_epg(channel_id, date):
    try:
        url = f"https://tm.tapi.tatasky.com/tata-sky-epg/v3/epg/channel/{channel_id}/date/{date}"
        r = session.get(url, headers=BASE_HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        return r.json().get("programmes", [])
    except Exception:
        return []

# --------------- JIOTV EPG --------------
def jio_epg(channel_id):
    try:
        url = "https://jiotvapi.media.jio.com/apis/v1.4/getepg/get"
        headers = {
            **BASE_HEADERS,
            "Referer": "https://www.jiotv.com/",
            "Origin": "https://www.jiotv.com"
        }
        r = session.get(url, headers=headers, params={"channel_id": channel_id}, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        return r.json().get("epg", [])
    except Exception:
        return []

# --------------- GENERATE EPG -----------
now = datetime.now(TZ)

for ch in channels:
    # Tata Play (primary)
    for d in range(DAYS):
        date = (now + timedelta(days=d)).strftime("%Y-%m-%d")
        programs = tata_epg(ch.get("tata_id"), date)

        for p in programs:
            try:
                start = datetime.fromtimestamp(p["startTime"] / 1000, TZ)
                stop = datetime.fromtimestamp(p["endTime"] / 1000, TZ)

                pr = etree.SubElement(
                    root,
                    "programme",
                    channel=ch["id"],
                    start=start.strftime("%Y%m%d%H%M%S %z"),
                    stop=stop.strftime("%Y%m%d%H%M%S %z")
                )
                etree.SubElement(pr, "title").text = p.get("title", "N/A")
                etree.SubElement(pr, "desc").text = p.get("description", "")
            except Exception:
                continue

    # JioTV (fallback / today only)
    for p in jio_epg(ch.get("jio_id")):
        try:
            start = datetime.fromtimestamp(int(p["start_time"]), TZ)
            stop = datetime.fromtimestamp(int(p["end_time"]), TZ)

            pr = etree.SubElement(
                root,
                "programme",
                channel=ch["id"],
                start=start.strftime("%Y%m%d%H%M%S %z"),
                stop=stop.strftime("%Y%m%d%H%M%S %z")
            )
            etree.SubElement(pr, "title").text = p.get("showname", "N/A")
            etree.SubElement(pr, "desc").text = p.get("description", "")
        except Exception:
            continue

# --------------- WRITE FILE -------------
tree = etree.ElementTree(root)
tree.write(
    "hybrid-epg.xml",
    pretty_print=True,
    encoding="UTF-8",
    xml_declaration=True
)

print("✅ Hybrid EPG generated successfully")
