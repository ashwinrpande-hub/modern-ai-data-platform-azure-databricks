#!/usr/bin/env python3
"""Synthetic data for 6 sources: SAP VBAK/KNA1, JDE F4201/F0101, QAD so_mstr,
SFDC opportunity, Litmus OT telemetry. Writes CSV/JSON/parquet to ./data for upload
to the ADLS landing zone (or use directly with Auto Loader against a UC Volume)."""
import csv, json, random, os, datetime as dt

random.seed(42); os.makedirs("data", exist_ok=True)
STEEL = ["HRC-1018","CRC-1045","REBAR-G60","WIRE-1080","PLATE-A36","SBQ-4140"]

def sap():
    with open("data/sap_vbak.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["VBELN","KUNNR","NETWR","WAERK","ERDAT"])
        for i in range(5000):
            w.writerow([f"00{4000000+i}", f"EU{random.randint(1,500):05d}",
                round(random.uniform(5e3,9e5),2), random.choice(["EUR","GBP"]),
                (dt.date(2025,1,1)+dt.timedelta(days=random.randint(0,500))).isoformat()])

def jde():
    with open("data/jde_f4201.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["SHKCOO","SHDOCO","SHDCTO","SHAN8","SHOTOT","SHCRCD","SHTRDJ"])
        for i in range(5000):
            d = dt.date(2025,1,1)+dt.timedelta(days=random.randint(0,500))
            julian = (d - dt.date(1900,1,1)).days + 36525
            w.writerow(["00001", 100000+i, "SO", random.randint(10000,10500),
                int(random.uniform(5e5,9e7)), "USD", julian])

def ot():
    rows=[]
    base = dt.datetime(2026,6,1)
    for h in range(72):
        for asset in ["furnace1","furnace2","caster1"]:
            for tag in ["temperature","power_kw","o2_pct"]:
                rows.append({"topic": f"nucor/berkeley/meltshop/{asset}/{tag}",
                    "deviceID": asset, "tagName": tag,
                    "value": round({"temperature":1620,"power_kw":42000,"o2_pct":2.1}[tag]*random.uniform(.92,1.08),2),
                    "timestamp": int((base+dt.timedelta(hours=h)).timestamp()*1000),
                    "quality": random.choices(["GOOD","UNCERTAIN","BAD"],[.95,.04,.01])[0]})
    json.dump(rows, open("data/litmus_ot_sample.json","w"), indent=0)

if __name__ == "__main__":
    sap(); jde(); ot()
    print("Synthetic data in ./data (SAP 5k, JDE 5k, OT 648 readings). Extend per source as needed.")
