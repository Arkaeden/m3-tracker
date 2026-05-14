import json
from curl_cffi import requests
from datetime import datetime
import os

# SONIC AUTOMOTIVE GROUP (Verified Working)
SONIC_DEALERS = [
    {"name": "East Bay BMW", "url": "https://www.eastbaybmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "Weatherford BMW", "url": "https://www.weatherfordbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "Stevens Creek BMW", "url": "https://www.stevenscreekbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "BMW of Mountain View", "url": "https://www.bmwofmountainview.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "Peter Pan BMW", "url": "https://www.peterpanbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "BMW of Fremont", "url": "https://www.bmwoffremont.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "BMW Concord", "url": "https://www.bmwconcord.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"}
]

def fetch_inventory():
    found_vins = {}
    
    with requests.Session() as s:
        # 1. SCAN SONIC SQUADRON
        for dealer in SONIC_DEALERS:
            print(f"--- SCANNING: {dealer['name']} ---")
            try:
                response = s.get(dealer['url'], impersonate="chrome124", timeout=25)
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
                                "link": f"https://www.{dealer['name'].replace(' ', '').lower()}.com/new/{vin}.htm"
                            }
            except Exception as e: print(f"Error at {dealer['name']}: {e}")

        # 2. SCAN THE CORPORATE TUNNEL (SF & SHADOW SCAN)
        print(f"--- SCANNING: BMW USA CORPORATE ORACLE (SF ZIP 94103) ---")
        try:
            # We hit the national inventory API using a 50-mile radius from SF
            oracle_url = "https://www.bmwusa.com/inventory/api/v1/search"
            params = {
                "zipCode": "94103",
                "radius": 50,
                "size": 100,
                "models": ["M3", "M4"],
                "type": "NEW"
            }
            # Mandatory headers to look like the My BMW App
            headers = {
                "Referer": "https://www.bmwusa.com/inventory.html",
                "Accept": "application/json"
            }
            r = s.get(oracle_url, params=params, headers=headers, impersonate="chrome124", timeout=30)
            
            if r.status_code == 200:
                oracle_data = r.json()
                listings = oracle_data.get('results', [])
                for car in listings:
                    vin = car.get('vin')
                    # If this VIN hasn't been found by the Sonic scraper, it's a "Shadow" car (like SF)
                    if vin and vin not in found_vins:
                        dealer_name = car.get('dealerName', 'BMW Center')
                        model_label = car.get('modelName', '').upper()
                        type_tag = "M4" if "M4" in model_label else "M3"
                        price = str(car.get('msrp', 'Call')).replace('$', '').replace(',', '').strip()
                        
                        found_vins[vin] = {
                            "vin": vin,
                            "year": car.get('year', '2026'),
                            "model": f"{type_tag} Competition" if 'COMPETITION' in car.get('trimName', '').upper() else type_tag,
                            "price": f"${price}" if price.isdigit() else "Call",
                            "color": car.get('exteriorColor', 'Check Dealer'),
                            "dealer": dealer_name,
                            "status": "On Lot" if car.get('availability') == "IN_STOCK" else "Arriving Soon",
                            "link": f"https://www.bmwusa.com/inventory.html#!/view/{vin}"
                        }
                        print(f" [✓] Oracle Found: {type_tag} at {dealer_name}")
            else:
                print(f" [!] Oracle Blocked (Code: {r.status_code}).")
        except Exception as e:
            print(f" [!] Oracle Logic Error: {e}")

    # 3. SAVE RESULTS
    if found_vins:
        output = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT"),
            "vehicles": list(found_vins.values())
        }
        with open('data.json', 'w') as f:
            json.dump(output, f, indent=4)
        print(f"\nSUCCESS: {len(found_vins)} M-Cars archived.")

if __name__ == "__main__":
    fetch_inventory()
