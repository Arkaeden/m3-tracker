import json
from curl_cffi import requests
from datetime import datetime
import re

# THE BAY AREA SQUADRON (SONIC GROUP)
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
        # 1. SCAN SONIC DEALERS
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
                            price_val = str(car.get('askingPrice', 'Call')).replace('$', '').strip()
                            found_vins[vin] = {
                                "vin": vin,
                                "year": car.get('modelYear', '2026'),
                                "model": f"{type_tag} Competition" if 'Comp' in car.get('trim', '') else type_tag,
                                "price": price_val if price_val == "Call" else f"${price_val}",
                                "color": car.get('exteriorColor', 'Check Dealer'),
                                "dealer": dealer['name'],
                                "status": "In Transit" if car.get('inTransit') else "On Lot",
                                "link": f"https://www.{dealer['name'].replace(' ', '').lower()}.com/new/{vin}.htm"
                            }
            except Exception as e: print(f"Error at {dealer['name']}: {e}")

        # 2. SCAN BMW OF SAN FRANCISCO (WITH PROXY FALLBACK)
        print(f"--- SCANNING: BMW of San Francisco ---")
        sf_success = False
        try:
            # TRY DIRECT AI PORTAL FIRST
            sf_url = "https://www.bmwsf.com/llm/inventory/"
            r = s.get(sf_url, impersonate="chrome124", timeout=15)
            
            if r.status_code == 200:
                # Direct match logic...
                sf_success = True
            elif r.status_code == 403:
                print(" [!] SF Direct Blocked (403). Pivoting to Proxy Scan...")
                # FALLBACK: Scan the SF Dealer Feed on Cars.com (Dealer ID: 5394476)
                proxy_url = "https://www.cars.com/shopping/results/?dealer_id=5394476&make_slugs[]=bmw&model_slugs[]=bmw-m3&model_slugs[]=bmw-m4&stock_type=new"
                pr = s.get(proxy_url, impersonate="chrome124", timeout=20)
                
                if pr.status_code == 200:
                    # Look for the hidden JSON payload in the Cars.com page
                    json_blob = re.search(r'window\.SEARCH_RESULTS\s*=\s*({.*?});', pr.text)
                    if json_blob:
                        search_data = json.loads(json_blob.group(1))
                        for car in search_data.get('results', []):
                            vin = car.get('vin')
                            if vin and vin.startswith('WBS'):
                                type_tag = "M4" if "m4" in car.get('model_label', '').lower() else "M3"
                                found_vins[vin] = {
                                    "vin": vin,
                                    "year": car.get('year', '2026'),
                                    "model": f"{type_tag} Competition" if 'Competition' in car.get('trim_label', '') else type_tag,
                                    "price": f"${car.get('price', 'Call')}",
                                    "color": car.get('exterior_color_label', 'Check Dealer'),
                                    "dealer": "BMW of San Francisco",
                                    "status": "On Lot",
                                    "link": f"https://www.cars.com/vehicledetail/{car.get('id')}/"
                                }
                                print(f" [✓] Added SF (via Proxy) {type_tag}: {vin[-6:]}")
                        sf_success = True
        except Exception as e:
            print(f" [!] SF Fallback Failed: {e}")

    # 3. SAVE TO DATA.JSON
    if found_vins:
        output = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT"),
            "vehicles": list(found_vins.values())
        }
        with open('data.json', 'w') as f:
            json.dump(output, f, indent=4)
        print(f"\nSUCCESS: {len(found_vins)} M-Cars archived.")
    else:
        print("\nCRITICAL: 0 allocations found.")

if __name__ == "__main__":
    fetch_inventory()
