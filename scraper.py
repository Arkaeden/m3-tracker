import json
from curl_cffi import requests
from datetime import datetime
import os

# SONIC GROUP (Mountain View, East Bay, etc.)
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

        # 2. SCAN BMW OF SAN FRANCISCO (Lithia/Sincro Logic)
        print(f"--- SCANNING: BMW of San Francisco ---")
        try:
            # SF requires a Referer header to unlock the JSON data
            sf_headers = {
                "Referer": "https://www.bmwsf.com/new-inventory/index.htm",
                "Accept": "application/json"
            }
            # This is the verified Sincro JSON search endpoint for Lithia
            sf_url = "https://www.bmwsf.com/inventory/search.json?stock_type=new&make=BMW&model=M3,M4"
            r = s.get(sf_url, headers=sf_headers, impersonate="chrome124", timeout=25)
            
            if r.status_code == 200:
                sf_data = r.json()
                # Sincro nests vehicles inside a 'vehicles' list
                for car in sf_data.get('vehicles', []):
                    vin = car.get('vin', '')
                    if vin.startswith('WBS'):
                        model_name = car.get('model_name', 'M3')
                        type_tag = "M4" if "M4" in model_name else "M3"
                        price = str(car.get('internet_price', 'Call')).replace('$', '').strip()
                        
                        found_vins[vin] = {
                            "vin": vin,
                            "year": car.get('model_year', '2026'),
                            "model": f"{type_tag} Competition" if 'Competition' in car.get('trim_name', '') else type_tag,
                            "price": price if price == "Call" else f"${price}",
                            "color": car.get('ext_color_generic', car.get('ext_color', 'Check Dealer')),
                            "dealer": "BMW of San Francisco",
                            "status": "On Lot",
                            "link": f"https://www.bmwsf.com/inventory/{car.get('slug', vin)}"
                        }
                        print(f" [✓] Added SF {type_tag}: {vin[-6:]}")
            else:
                print(f" [!] SF Status: {r.status_code} - Possible Firewall Block")
        except Exception as e:
            print(f" [!] SF Logic Error: {e}")

    # SAVE TO DATA.JSON
    if found_vins:
        output = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT"),
            "vehicles": list(found_vins.values())
        }
        with open('data.json', 'w') as f:
            json.dump(output, f, indent=4)
        print(f"\nSUCCESS: {len(found_vins)} M-Cars archived.")
    else:
        print("\nCRITICAL: No allocations found.")

if __name__ == "__main__":
    fetch_inventory()
