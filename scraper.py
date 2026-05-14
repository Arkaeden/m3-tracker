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

# The robot will now look for these strings anywhere in the vehicle's name
TARGET_MODELS = ["M3", "M4"]

def fetch_inventory():
    existing_vehicles = []
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
                existing_vehicles = data.get('vehicles', [])
        except: pass

    found_vins = {}
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'darwin','desktop': True})

    for dealer in DEALERS:
        try:
            # We now pull the ENTIRE BMW inventory for the dealer
            response = scraper.get(dealer['url'], timeout=20)
            if response.status_code == 200:
                data = response.json()
                if 'pageInfo' in data and 'trackingData' in data['pageInfo']:
                    for car in data['pageInfo']['trackingData']:
                        model_str = car.get('model', '')
                        
                        # Check if EITHER M3 or M4 is in the model name
                        for target in TARGET_MODELS:
                            if target in model_str:
                                vin = car.get('vin', 'N/A')
                                if vin in found_vins: continue

                                found_vins[vin] = {
                                    "vin": vin,
                                    "year": car.get('modelYear', '2024'),
                                    "model": f"{target} Competition" if 'Comp' in car.get('trim', '') else target,
                                    "price": f"${car.get('askingPrice', 'Call')}",
                                    "color": car.get('exteriorColor', 'Check Dealer'),
                                    "dealer": dealer['name'],
                                    "status": "In Transit" if car.get('inTransit') else "On Lot",
                                    "image": "PENDING",
                                    "link": f"https://www.{dealer['name'].replace(' ', '').lower()}.com/new/{vin}.htm",
                                    "is_new": True 
                                }
        except Exception as e:
            print(f"Error at {dealer['name']}: {e}")
            
    # Compile the final list
    final_vehicles = list(found_vins.values())
    
    # If the scan actually found cars, we use them. Otherwise, we keep the old data so the site doesn't go blank.
    if not final_vehicles:
        final_vehicles = existing_vehicles

    output = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT"),
        "vehicles": final_vehicles
    }
    
    with open('data.json', 'w') as f:
        json.dump(output, f, indent=4)

if __name__ == "__main__":
    fetch_inventory()
