#!/usr/bin/env python3
"""Synthetic data — now covers ALL registered sources (gap B6): SAP VBAK+KNA1,
JDE F4201+F0101, QAD so_mstr, SFDC opportunity, D365 salesorders, Litmus OT.
Product codes (STEEL) now emitted -> enables a future dim_product."""
import csv, json, random, os, datetime as dt

random.seed(42); os.makedirs("data", exist_ok=True)
STEEL = ["HRC-1018","CRC-1045","REBAR-G60","WIRE-1080","PLATE-A36","SBQ-4140"]

def _date(): return dt.date(2025,1,1)+dt.timedelta(days=random.randint(0,500))

def sap():
    with open("data/sap_vbak.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["VBELN","KUNNR","NETWR","WAERK","ERDAT","MATNR"])
        for i in range(5000):
            w.writerow([f"00{4000000+i}", f"EU{random.randint(1,500):05d}",
                round(random.uniform(5e3,9e5),2), random.choice(["EUR","GBP"]),
                _date().isoformat(), random.choice(STEEL)])
    with open("data/sap_kna1.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["KUNNR","NAME1","LAND1"])
        for i in range(1,501):
            w.writerow([f"EU{i:05d}", f"EU Steelworks {i} GmbH",
                        random.choice(["DE","FR","IT","ES","PL"])])

def jde():
    with open("data/jde_f4201.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["SHKCOO","SHDOCO","SHDCTO","SHAN8","SHOTOT","SHCRCD","SHTRDJ","SHLITM"])
        for i in range(5000):
            d=_date(); julian=(d-dt.date(1900,1,1)).days+36525
            w.writerow(["00001", 100000+i, "SO", random.randint(10000,10500),
                int(random.uniform(5e5,9e7)), "USD", julian, random.choice(STEEL)])
    with open("data/jde_f0101.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["ABAN8","ABALPH","ABCTR"])
        for i in range(10000,10501):
            w.writerow([i, f"Americas Metals {i} Inc", random.choice(["US","CA","MX"])])

def qad():
    with open("data/qad_so_mstr.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["so_domain","so_nbr","so_cust","so_t_amt","so_curr","so_ord_date","so_part"])
        for i in range(3000):
            w.writerow(["EMEA", f"SO{700000+i}", f"ME{random.randint(1,300):04d}",
                round(random.uniform(4e3,6e5),2), random.choice(["EUR","USD"]),
                _date().isoformat(), random.choice(STEEL)])

def sfdc():
    rows=[{"Id": f"006{i:015d}", "AccountId": f"001{random.randint(1,800):015d}",
           "Amount": round(random.uniform(1e4,2e6),2), "StageName":
           random.choices(["Prospecting","Proposal","Closed Won","Closed Lost"],[.3,.3,.25,.15])[0],
           "Product__c": random.choice(STEEL),
           "SystemModstamp": (dt.datetime(2025,1,1)+dt.timedelta(hours=random.randint(0,12000))).isoformat()+"Z"}
          for i in range(2000)]
    json.dump(rows, open("data/sfdc_opportunity.json","w"), indent=0)

def d365():
    rows=[{"salesorderid": f"d365-{i:08d}", "customerid": f"acct-{random.randint(1,400):05d}",
           "totalamount": round(random.uniform(8e3,1.2e6),2), "transactioncurrencyid": "USD",
           "productcode": random.choice(STEEL),
           "modifiedon": (dt.datetime(2025,6,1)+dt.timedelta(hours=random.randint(0,8000))).isoformat()+"Z"}
          for i in range(1500)]
    json.dump(rows, open("data/d365_salesorders.json","w"), indent=0)

def ot():
    rows=[]; base=dt.datetime(2026,6,1)
    for h in range(72):
        for asset in ["furnace1","furnace2","caster1"]:
            for tag in ["temperature","power_kw","o2_pct"]:
                rows.append({"topic": f"acme/berkeley/meltshop/{asset}/{tag}",
                    "deviceID": asset, "tagName": tag,
                    "value": round({"temperature":1620,"power_kw":42000,"o2_pct":2.1}[tag]*random.uniform(.92,1.08),2),
                    "timestamp": int((base+dt.timedelta(hours=h)).timestamp()*1000),
                    "quality": random.choices(["GOOD","UNCERTAIN","BAD"],[.95,.04,.01])[0]})
    json.dump(rows, open("data/litmus_ot_sample.json","w"), indent=0)

def mes():
    rows=[{"topic": f"acme/berkeley/rollmill/mes/order_{ev}",
           "work_order_id": f"WO{80000+i}", "event": ev, "product": random.choice(STEEL),
           "ts": int((dt.datetime(2026,6,1)+dt.timedelta(minutes=15*i)).timestamp()*1000)}
          for i in range(1000) for ev in (["start","complete"] if i%2==0 else ["start"])]
    json.dump(rows, open("data/mes_rollmill.json","w"), indent=0)

if __name__ == "__main__":
    sap(); jde(); qad(); sfdc(); d365(); ot(); mes()
    print("Synthetic data in ./data: SAP 5k+500, JDE 5k+501, QAD 3k, SFDC 2k, D365 1.5k, "
          "OT 648, MES ~1.5k. Product codes included for dim_product.")

