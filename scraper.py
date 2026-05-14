import json
import cloudscraper
from datetime import datetime
import os

# CONFIGURATION
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
        except:
            pass

    # Use a dictionary to avoid duplicates by VIN
    found_vins = {}
    
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'darwin',
        'desktop': True
    })

    for dealer in DEALERS:
        for model_name in TARGET_MODELS:
            search_url = f"{dealer['url']}&model={model_name}"
            try:
                response = scraper.get(search_url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    # Check for typical BMW widget data structure
                    if 'pageInfo' in data and 'trackingData' in data['pageInfo']:
                        for car in data['pageInfo']['trackingData']:
                            # Double check the model string in case the API returns nearby matches
                            if model_name in car.get('model', ''):
                                vin = car.get('vin', 'N/A')
                                
                                # Skip if we've already processed this VIN in this run
                                if vin in found_vins: continue

                                # Image resolution
                                raw_img = car.get('imageUrl') or car.get('imageURL') or car.get('primaryImage') or ''
                                if not raw_img or 'placeholder' in raw_img:
                                    raw_img = 'PENDING' # UI will handle the asset mapping

                                found_vins[vin] = {
                                    "vin": vin,
                                    "year": car.get('modelYear', '2024'),
                                    "model": f"{model_name} Competition" if 'Comp' in car.get('trim', '') else model_name,
                                    "price": f"${car.get('askingPrice', 'Call')}",
                                    "color": car.get('exteriorColor', 'Check Dealer'),
                                    "dealer": dealer['name'],
                                    "status": "In Transit" if car.get('inTransit') else "On Lot",
                                    "image": raw_img,
                                    "link": f"https://www.{dealer['name'].replace(' ', '').lower()}.com/new/{vin}.htm",
                                    "is_new": True 
                                }
            except Exception:
                pass 
            
    # Compile final list
    final_vehicles = list(found_vins.values())
    
    # Fail-safe: if scan fails entirely, keep existing data
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
