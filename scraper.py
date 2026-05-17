import json
from curl_cffi import requests
from datetime import datetime
import os
import time  # New engine component for automated throttling

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
    
    # Premium user-agent masking to slip past 403 firewall parameters
    custom_headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    with requests.Session() as s:
        s.headers.update(custom_headers)
        
        for dealer in SONIC_DEALERS:
            dealer_count = 0
            print(f"--- SCANNING: {dealer['name']} ---")
            
            for model_target in ["M3", "M4"]:
                # Primary modern widget path
                url = f"https://www.{dealer['domain']}/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model={model_target}"
                
                try:
                    response = s.get(url, impersonate="chrome124", timeout=25)
                    
                    # Fallback mechanism if a dealer throws a 404 (Migrated to Bus2 routing architecture)
                    if response.status_code == 404:
                        url = f"https://www.{dealer['domain']}/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus2/getInventory?make=BMW&model={model_target}"
                        response = s.get(url, impersonate="chrome124", timeout=25)

                    if response.status_code == 200:
                        data = response.json()
                        cars = data.get('pageInfo', {}).get('trackingData', [])
                        
                        for car in cars:
                            vin = car.get('vin', 'N/A')
                            model_str = car.get('model', '')
                            
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
                                
                    elif response.status_code == 429:
                        print(f" [!] Warning: Throttled by {dealer['name']} on [{model_target}] query.")
                    else:
                        print(f" [!] Connection Bypass Failed: {dealer['name']} returned {response.status_code} for {model_target}")
                        
                except Exception as e:
                    print(f" [!] Pipeline latency error at {dealer['name']} [{model_target}]: {e}")
                
                # HUMANIZING DELAY: Pause for 3 seconds between model strikes to prevent 429 triggers
                time.sleep(3.0)
            
            print(f" >> SQUADRON LOG: {dealer['name']} verified at [{dealer_count} UNITS]")
            # Brief cool-off pause between separate dealerships
            time.sleep(1.5)

    # OUTPUT GENERATION
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
