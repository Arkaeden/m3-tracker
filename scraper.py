import json
from curl_cffi import requests
from datetime import datetime
import re

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

        # 2. SCAN BMW OF SAN FRANCISCO (The AI Portal)
        print(f"--- SCANNING: BMW of San Francisco (AI PORTAL) ---")
        try:
            # We target their specific AI-friendly inventory page
            sf_url = "https://www.bmwsf.com/llm/inventory/"
            r = s.get(sf_url, impersonate="chrome124", timeout=25)
            
            if r.status_code == 200:
                # We use regex to find the VINs and details in the text table
                # Format is: 2026 BMW M3 Competition (VIN: WBS...) | Type | Color | Mileage | Price | Link
                rows = re.findall(r'(\d{4})\s(BMW\sM[34]\s[^|]+)\(VIN:\s([A-Z0-9]+)\)\s\|\s[^|]+\s\|\s([^|]+)\s\|\s[^|]+\s\|\s\$?([\d,]+|Call)\s\|\s\[View Details\]\(([^)]+)\)', r.text)
                
                for row in rows:
                    year, model_name, vin, color, price, link = row
                    if vin.startswith('WBS'):
                        type_tag = "M4" if "M4" in model_name else "M3"
                        found_vins[vin] = {
                            "vin": vin,
                            "year": year,
                            "model": f"{type_tag} Competition" if 'Competition' in model_name else type_tag,
                            "price": f"${price.strip()}" if price != "Call" else "Call",
                            "color": color.strip(),
                            "dealer": "BMW of San Francisco",
                            "status": "On Lot",
                            "link": f"https://www.bmwsf.com{link}" if link.startswith('/') else link
                        }
                        print(f" [✓] Added SF {type_tag}: {vin[-6:]}")
            else:
                print(f" [!] SF Status: {r.status_code}. The AI Portal might be down.")
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

if __name__ == "__main__":
    fetch_inventory()
