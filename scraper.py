import json
from curl_cffi import requests
from datetime import datetime
import re

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
                            # Aggressive Price Cleaning
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

        # 2. SCAN BMW OF SAN FRANCISCO (TRUECAR PROXY)
        print(f"--- SCANNING: BMW of San Francisco (TRUECAR PIVOT) ---")
        try:
            # Targeting BMW of SF via TrueCar (Dealer ID 34336)
            tc_url = "https://www.truecar.com/new-cars-for-sale/listings/bmw/m3/location-san-francisco-ca/?dealer_id=34336"
            tr = s.get(tc_url, impersonate="chrome124", timeout=25)
            
            if tr.status_code == 200:
                # TrueCar stores everything in a clean JSON block called '__NEXT_DATA__'
                json_blob = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', tr.text)
                if json_blob:
                    raw_data = json.loads(json_blob.group(1))
                    listings = raw_data.get('props', {}).get('pageProps', {}).get('listings', [])
                    
                    for car in listings:
                        vin = car.get('vin')
                        if vin and vin.startswith('WBS'):
                            model_name = car.get('model', 'M3')
                            type_tag = "M4" if "M4" in model_name else "M3"
                            price = str(car.get('pricing', {}).get('msrp', 'Call')).replace('$', '').replace(',', '').strip()
                            
                            found_vins[vin] = {
                                "vin": vin,
                                "year": car.get('year', '2026'),
                                "model": f"{type_tag} Competition" if 'Competition' in car.get('trim', '') else type_tag,
                                "price": f"${price}" if price.isdigit() else "Call",
                                "color": car.get('exteriorColor', 'Check Dealer'),
                                "dealer": "BMW of San Francisco",
                                "status": "On Lot",
                                "link": f"https://www.bmwsf.com/inventory/new-{car.get('year')}-bmw-{type_tag.lower()}-{vin}/"
                            }
                            print(f" [✓] Added SF (via TrueCar) {type_tag}: {vin[-6:]}")
                else:
                    print(" [!] SF Pivot Error: JSON Payload Hidden.")
            else:
                print(f" [!] SF Pivot Blocked. Status: {tr.status_code}")
        except Exception as e:
            print(f" [!] SF TrueCar Logic Error: {e}")

    # 3. SAVE RESULTS
    if found_vins:
        output = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT"),
            "vehicles": len(found_vins),
            "vehicles": list(found_vins.values())
        }
        with open('data.json', 'w') as f:
            json.dump(output, f, indent=4)
        print(f"\nSUCCESS: {len(found_vins)} M-Cars archived.")

if __name__ == "__main__":
    fetch_inventory()
