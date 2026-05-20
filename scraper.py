import json
import random  
from curl_cffi import requests
from datetime import datetime
import os
import time

# SQUADRON REGISTRY
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
            
            s.headers.update({
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": f"https://www.{dealer['domain']}/new-inventory/index.htm",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            })
            
            for model_target in ["M3", "M4"]:
                attempts = 0
                max_attempts = 3  
                success = False
                
                endpoints = [
                    f"https://www.{dealer['domain']}/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model={model_target}",
                    f"https://www.{dealer['domain']}/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus2/getInventory?make=BMW&model={model_target}",
                    f"https://www.{dealer['domain']}/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus/getInventory?make=BMW&model={model_target}"
                ]
                
                current_endpoint_idx = 0
                
                while attempts < max_attempts and not success and current_endpoint_idx < len(endpoints):
                    url = endpoints[current_endpoint_idx]
                    try:
                        response = s.get(url, impersonate="chrome124", timeout=25)
                        
                        if response.status_code == 404:
                            current_endpoint_idx += 1
                            continue

                        if response.status_code == 200:
                            data = response.json()
                            
                            cars = data.get('pageInfo', {}).get('trackingData', [])
                            if not cars and 'vehicles' in data:
                                cars = data.get('vehicles', [])
                            if not cars and 'pageInfo' in data and 'vehicles' in data.get('pageInfo', {}):
                                cars = data.get('pageInfo', {}).get('vehicles', [])

                            for car in cars:
                                vin = car.get('vin') or car.get('vinCode') or 'N/A'
                                model_str = car.get('model') or car.get('modelName') or ''
                                
                                if vin.startswith('WBS') and not any(x in model_str for x in ["340", "440"]):
                                    type_tag = "M4" if "M4" in model_str else "M3"
                                    
                                    asking_p = car.get('askingPrice') or car.get('msrp') or car.get('internetPrice') or 'Call'
                                    raw_p = str(asking_p).replace('$', '').replace(',', '').strip()
                                    color_meta = car.get('exteriorColor') or car.get('extColor') or 'Check Dealer'
                                    in_transit = car.get('inTransit') or car.get('isTransit') or (car.get('status', '').upper() == 'IN_TRANSIT')
                                    
                                    found_vins[vin] = {
                                        "vin": vin,
                                        "year": str(car.get('modelYear') or car.get('year') or '2026'),
                                        "model": f"{type_tag} Competition" if 'Comp' in str(car.get('trim', '') or car.get('trimName', '')) else type_tag,
                                        "price": f"${raw_p}" if raw_p.isdigit() else "Call",
                                        "color": color_meta,
                                        "dealer": dealer['name'],
                                        "status": "In Transit" if in_transit else "On Lot",
                                        "link": f"https://www.{dealer['domain']}/new/{vin}.htm"
                                    }
                                    dealer_count += 1
                            success = True
                            
                        elif response.status_code == 429:
                            attempts += 1
                            if attempts < max_attempts:
                                penalty = (8.0 * attempts) + random.uniform(1.0, 3.0)
                                print(f" [!] Rate limited by {dealer['name']}. Deploying evasion cool-off ({penalty:.1f}s)...")
                                time.sleep(penalty)
                            else:
                                print(f" [!] Connection Terminated: {dealer['name']} blocked request after max retries.")
                                success = True 
                        else:
                            print(f" [!] Request Bypass Refused: {dealer['name']} returned status code {response.status_code}")
                            success = True  
                            
                    except Exception as e:
                        print(f" [!] Pipeline error at {dealer['name']} [{model_target}]: {e}")
                        success = True
                
                time.sleep(random.uniform(4.0, 7.0))
            
            print(f" >> SQUADRON LOG: {dealer['name']} verified at [{dealer_count} UNITS]")
            time.sleep(random.uniform(2.5, 4.5))

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
