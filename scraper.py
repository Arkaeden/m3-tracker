import json
import cloudscraper
from datetime import datetime
import os

DEALERS = [
    {"name": "East Bay BMW", "url": "https://www.eastbaybmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW"},
    {"name": "Weatherford BMW", "url": "https://www.weatherfordbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW"},
    {"name": "Stevens Creek BMW", "url": "https://www.stevenscreekbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW"},
    {"name": "BMW of Mountain View", "url": "https://www.bmwofmountainview.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW"}
]

def fetch_inventory():
    found_vins = {}
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'darwin','desktop': True})

    for dealer in DEALERS:
        print(f"\n--- SCANNING: {dealer['name']} ---")
        try:
            response = scraper.get(dealer['url'], timeout=20)
            if response.status_code == 200:
                data = response.json()
                cars = data.get('pageInfo', {}).get('trackingData', [])
                print(f"Total BMWs scanned: {len(cars)}")
                
                for car in cars:
                    model_str = car.get('model', '')
                    vin = car.get('vin', 'N/A')
                    
                    # WBS = True M-Car Registry. This is our master filter.
                    is_m_car = vin.startswith('WBS')
                    is_target = "M3" in model_str or "M4" in model_str
                    is_lite = "440" in model_str or "340" in model_str # Excludes M440i / M340i

                    if is_m_car and is_target and not is_lite:
                        print(f"MATCH: {model_str} ({vin})")
                        
                        target_type = "M4" if "M4" in model_str else "M3"
                        found_vins[vin] = {
                            "vin": vin,
                            "year": car.get('modelYear', '2024'),
                            "model": f"{target_type} Competition" if 'Comp' in car.get('trim', '') else target_type,
                            "price": f"${car.get('askingPrice', 'Call')}",
                            "color": car.get('exteriorColor', 'Check Dealer'),
                            "dealer": dealer['name'],
                            "status": "In Transit" if car.get('inTransit') else "On Lot",
                            "image": "PENDING",
                            "link": f"https://www.{dealer['name'].replace(' ', '').lower()}.com/new/{vin}.htm",
                            "is_new": True 
                        }
            else:
                print(f"Blocked: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
            
    if found_vins:
        output = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT"), "vehicles": list(found_vins.values())}
        with open('data.json', 'w') as f:
            json.dump(output, f, indent=4)
        print(f"\nSUCCESS: {len(found_vins)} M-Cars archived.")
    else:
        print("\nZERO MATCHES: No M-Cars found in this inventory sweep.")

if __name__ == "__main__":
    fetch_inventory()
