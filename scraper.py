import json
from curl_cffi import requests
from datetime import datetime
import os

# CLEAN DOMAIN REGISTRY TO INSULATE AGAINST WIDGET VARIANCE
SONIC_DEALERS = [
    {"name": "East Bay BMW", "domain": "eastbaybmw.com"},
    {"name": "Weatherford BMW", "domain": "weatherfordbmw.com"},
    {"name": "Stevens Creek BMW", "domain": "stevenscreekbmw.com"},
    {"name": "BMW of Mountain View", "domain": "bmwofmountainview.com"},
    {"name": "Peter Pan BMW", "domain": "peterpanbmw.com"},
    {"name": "BMW of Fremont", "domain": "bmwoffremont.com"},
    {"name": "BMW Concord", "domain": "bmwconcord.com"}
]

def fetch_inventory():
    found_vins = {}
    
    with requests.Session() as s:
        for dealer in SONIC_DEALERS:
            dealer_count = 0
            print(f"--- SCANNING: {dealer['name']} ---")
            
            # Isolate the models into individual requests to bypass the comma-parsing restrictions
            for model_target in ["M3", "M4"]:
                url = f"https://www.{dealer['domain']}/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model={model_target}"
                
                try:
                    response = s.get(url, impersonate="chrome124", timeout=25)
                    if response.status_code == 200:
                        data = response.json()
                        cars = data.get('pageInfo', {}).get('trackingData', [])
                        
                        for car in cars:
                            vin = car.get('vin', 'N/A')
                            model_str = car.get('model', '')
                            
                            # Enforce strict M-GmbH validation (WBS chassis prefix only)
                            if vin.startswith('WBS') and not any(x in model_str for x in ["340", "440"]):
                                type_tag = "M4" if "M4" in model_str else "M3"
                                raw_p = str(car.get('askingPrice', 'Call')).replace('$', '').replace(',', '').strip()
                                
                                found_vins[vin] = {
                                    "vin": vin,
                                    "year": car.get('modelYear', '2026'),
                                    "model": f"{type_tag} Competition" if 'Comp' in car.get('trim', '') else type_tag,
                                    "price": f"${raw_p}" if raw_p.isdigit() else "Call",
                                    "color": car.get('exteriorColor', 'Check Dealer'),
                                    "dealer": dealer['name'],
                                    "status": "In Transit" if car.get('inTransit') else "On Lot",
                                    "link": f"https://www.{dealer['domain']}/new/{vin}.htm"
                                }
                                dealer_count += 1
                    else:
                        print(f" [!] {dealer['name']} responded with status: {response.status_code} for {model_target}")
                except Exception as e:
                    print(f" [!] Pipeline latency error at {dealer['name']} [{model_target}]: {e}")
            
            print(f" >> SQUADRON LOG: {dealer['name']} verified at [{dealer_count} UNITS]")

    # SAVE TO CORE DATABASE
    if found_vins:
        output = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT"),
            "vehicles": list(found_vins.values())
        }
        with open('data.json', 'w') as f:
            json.dump(output, f, indent=4)
        print(f"\nSUCCESS: {len(found_vins)} active allocations locked into data.json.")

if __name__ == "__main__":
    fetch_inventory()
