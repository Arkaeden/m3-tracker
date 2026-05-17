import json
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
            
            # Dynamic Referer Spoofing: Matches the specific dealer's internal domain structure
            s.headers.update({
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": f"https://www.{dealer['domain']}/new-inventory/index.htm",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            })
            
            for model_target in ["M3", "M4"]:
                # Primary modern widget path configuration
                url = f"https://www.{dealer['domain']}/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model={model_target}"
                
                attempts = 0
                max_attempts = 2
                success = False
                
                while attempts < max_attempts and not success:
                    try:
                        response = s.get(url, impersonate="chrome124", timeout=25)
                        
                        # Fallback mechanism if a dealer throws a 404 (Reroute to Bus2 setup)
                        if response.status_code == 404:
                            url = f"https://www.{dealer['domain']}/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus2/getInventory?make=BMW&model={model_target}"
                            response = s.get(url, impersonate="chrome124", timeout=25)
                        
                        # Fallback mechanism if a dealer throws a second 404 (Reroute to alternative corporate endpoint)
                        if response.status_code == 404:
                            url = f"https://www.{dealer['domain']}/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus3/getInventory?make=BMW&model={model_target}"
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
                            success = True
                            
                        elif response.status_code == 429:
                            attempts += 1
                            if attempts < max_attempts:
                                print(f" [!] Rate limited by {dealer['name']}. Deploying cool-off sequence (7s)...")
                                time.sleep(7.0)
                            else:
                                print(f" [!] Connection Terminated: {dealer['name']} blocked request after retry loop.")
                        else:
                            print(f" [!] Request Bypass Refused: {dealer['name']} returned status code {response.status_code}")
                            success = True  # Break out of loop for non-429 errors
                            
                    except Exception as e:
                        print(f" [!] Pipeline error at {dealer['name']} [{model_target}]: {e}")
                        success = True
                
                # Standard throttle safety window between model changes
                time.sleep(3.5)
            
            print(f" >> SQUADRON LOG: {dealer['name']} verified at [{dealer_count} UNITS]")
            time.sleep(2.0)

    # OUTPUT COMPILATION
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
