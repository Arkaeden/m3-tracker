import json
from curl_cffi import requests
from datetime import datetime
import os

# EXPANDED BAY AREA SQUADRON
DEALERS = [
    {"name": "East Bay BMW", "url": "https://www.eastbaybmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "Weatherford BMW", "url": "https://www.weatherfordbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "Stevens Creek BMW", "url": "https://www.stevenscreekbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "BMW of Mountain View", "url": "https://www.bmwofmountainview.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "Peter Pan BMW", "url": "https://www.peterpanbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "BMW of Fremont", "url": "https://www.bmwoffremont.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "BMW Concord", "url": "https://www.bmwconcord.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"},
    {"name": "BMW of San Francisco", "url": "https://www.bmwsf.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3,M4"}
]

def fetch_inventory():
    found_vins = {}
    
    with requests.Session() as s:
        for dealer in DEALERS:
            print(f"--- SCANNING: {dealer['name']} ---")
            try:
                response = s.get(
                    dealer['url'], 
                    impersonate="chrome124", 
                    timeout=25
                )
                
                if response.status_code == 200:
                    data = response.json()
                    cars = data.get('pageInfo', {}).get('trackingData', [])
                    
                    for car in cars:
                        vin = car.get('vin', 'N/A')
                        model_str = car.get('model', '')
                        
                        if vin.startswith('WBS') and not any(x in model_str for x in ["340", "440"]):
                            type_tag = "M4" if "M4" in model_str else "M3"
                            
                            # SOURCE-LEVEL PRICE CLEANING
                            raw_price = str(car.get('askingPrice', 'Call'))
                            clean_price = raw_price.replace('$', '').strip()
                            
                            found_vins[vin] = {
                                "vin": vin,
                                "year": car.get('modelYear', '2026'),
                                "model": f"{type_tag} Competition" if 'Comp' in car.get('trim', '') else type_tag,
                                "price": clean_price if clean_price == "Call" else f"${clean_price}",
                                "color": car.get('exteriorColor', 'Check Dealer'),
                                "dealer": dealer['name'],
                                "status": "In Transit" if car.get('inTransit') else "On Lot",
                                "image": "PENDING",
                                "link": f"https://www.{dealer['name'].replace(' ', '').lower()}.com/new/{vin}.htm",
                                "is_new": True 
                            }
                            print(f" [✓] Added {type_tag}: {vin[-6:]}")
                else:
                    print(f" [!] {dealer['name']} reported status: {response.status_code}")
            except Exception as e:
                print(f" [!] Connection Error: {e}")

    if found_vins:
        output = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT"),
            "vehicles": list(found_vins.values())
        }
        with open('data.json', 'w') as f:
            json.dump(output, f, indent=4)
        print(f"\nSUCCESS: {len(found_vins)} M-Cars saved.")
    else:
        print("\nCRITICAL: No allocations found.")

if __name__ == "__main__":
    fetch_inventory()
