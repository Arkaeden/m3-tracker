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
        for model_name in TARGET_MODELS:
            search_url = f"{dealer['url']}&model={model_name}"
            try:
                response = scraper.get(search_url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if 'pageInfo' in data and 'trackingData' in data['pageInfo']:
                        for car in data['pageInfo']['trackingData']:
                            if model_name in car.get('model', ''):
                                vin = car.get('vin', 'N/A')
                                if vin in found_vins: continue

                                found_vins[vin] = {
                                    "vin": vin,
                                    "year": car.get('modelYear', '2024'),
                                    "model": f"{model_name} Competition" if 'Comp' in car.get('trim', '') else model_name,
                                    "price": f"${car.get('askingPrice', 'Call')}",
                                    "color": car.get('exteriorColor', 'Check Dealer'),
                                    "dealer": dealer['name'],
                                    "status": "In Transit" if car.get('inTransit') else "On Lot",
                                    "image": "PENDING",
                                    "link": f"https://www.{dealer['name'].replace(' ', '').lower()}.com/new/{vin}.htm",
                                    "is_new": True 
                                }
            except Exception: pass 
            
    final_vehicles = list(found_vins.values()) if found_vins else existing_vehicles
    output = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT"), "vehicles": final_vehicles}
    
    with open('data.json', 'w') as f:
        json.dump(output, f, indent=4)

if __name__ == "__main__":
    fetch_inventory()
