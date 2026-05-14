import json
from curl_cffi import requests
from datetime import datetime
import os

# SPLIT DEALER LIST (SONIC VS LITHIA)
SONIC_DEALERS = [
    {"name": "East Bay BMW", "url": "https://www.eastbaybmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "Weatherford BMW", "url": "https://www.weatherfordbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "Stevens Creek BMW", "url": "https://www.stevenscreekbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "BMW of Mountain View", "url": "https://www.bmwofmountainview.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "Peter Pan BMW", "url": "https://www.peterpanbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "BMW of Fremont", "url": "https://www.bmwoffremont.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "BMW Concord", "url": "https://www.bmwconcord.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"}
]

# SF uses a completely different "LLM-Friendly" endpoint
SF_DEALER = {"name": "BMW of San Francisco", "url": "https://www.bmwsf.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"} # This will likely fail, we will add a fallback

def fetch_inventory():
    found_vins = {}
    
    with requests.Session() as s:
        # SCAN SONIC SQUADRON
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
                            
                            # PRICE CLEANING
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

        # SPECIAL SCAN FOR SAN FRANCISCO (Sincro/Lithia Path)
        # Note: If their widget API stays blocked, we use their 'llm' path in the next version
        print(f"--- SCANNING: BMW of San Francisco ---")
        try:
            # We'll try their standard search API first
            sf_url = "https://www.bmwsf.com/inventory/search.json?stock_type=new&make=BMW&model=M3,M4"
            r = s.get(sf_url, impersonate="chrome124", timeout=25)
            if r.status_code == 200:
                sf_data = r.json()
                for car in sf_data.get('vehicles', []):
                    vin = car.get('vin')
                    if vin and vin.startswith('WBS'):
                        found_vins[vin] = {
                            "vin": vin,
                            "year": car.get('year'),
                            "model": car.get('model'),
                            "price": f"${car.get('price')}",
                            "color": car.get('exterior_color'),
                            "dealer": "BMW of San Francisco",
                            "status": "In Stock",
                            "link": f"https://www.bmwsf.com/inventory/{car.get('slug')}"
                        }
        except: print("SF Scan failed. They might have changed their JSON path.")

    if found_vins:
        output = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT"), "vehicles": list(found_vins.values())}
        with open('data.json', 'w') as f: json.dump(output, f, indent=4)
        print(f"SUCCESS: {len(found_vins)} M-Cars archived.")

if __name__ == "__main__":
    fetch_inventory()
