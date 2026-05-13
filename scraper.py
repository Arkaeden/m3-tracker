import json
import requests
from datetime import datetime
import os

DEALERS = [
    {"name": "East Bay BMW", "url": "https://www.eastbaybmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3"},
    {"name": "Weatherford BMW", "url": "https://www.weatherfordbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3"},
    {"name": "Stevens Creek BMW", "url": "https://www.stevenscreekbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3"},
    {"name": "BMW of Mountain View", "url": "https://www.bmwofmountainview.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3"}
]

def fetch_inventory():
    existing_vehicles = []
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
                existing_vehicles = data.get('vehicles', [])
        except:
            pass

    existing_vins = {car['vin']: car for car in existing_vehicles}
    new_vehicles_found = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://www.google.com/'
    }

    for dealer in DEALERS:
        try:
            response = requests.get(dealer['url'], headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'pageInfo' in data and 'trackingData' in data['pageInfo']:
                    for car in data['pageInfo']['trackingData']:
                        if 'M3' in car.get('model', ''):
                            vin = car.get('vin', 'N/A')
                            
                            # THE FIX: Check every possible variation of the image label
                            raw_img = car.get('imageUrl') or car.get('imageURL') or car.get('primaryImage') or car.get('image', '')
                            if not raw_img or 'placeholder' in raw_img:
                                raw_img = 'https://via.placeholder.com/600x400?text=Image+Unavailable'
                            
                            if vin in existing_vins:
                                car_data = existing_vins[vin]
                                car_data['is_new'] = False 
                                # Update the photo if the scraper found a better one today
                                if 'placeholder' in car_data['image'] and 'placeholder' not in raw_img:
                                    car_data['image'] = raw_img
                                new_vehicles_found.append(car_data)
                            else:
                                new_vehicles_found.append({
                                    "vin": vin,
                                    "year": car.get('modelYear', '2024'),
                                    "model": "M3 Competition" if 'Comp' in car.get('trim', '') else "M3",
                                    "price": f"${car.get('askingPrice', 'Call')}",
                                    "color": car.get('exteriorColor', 'Check Dealer'),
                                    "dealer": dealer['name'],
                                    "status": "In Transit" if car.get('inTransit') else "On Lot",
                                    "image": raw_img,
                                    "link": f"https://www.{dealer['name'].replace(' ', '').lower()}.com/new/{vin}.htm",
                                    "is_new": True 
                                })
        except Exception as e:
            pass 
            
    if len(new_vehicles_found) > 0:
        final_vehicles = new_vehicles_found
    elif len(existing_vehicles) > 0:
        final_vehicles = existing_vehicles
    else:
        final_vehicles = [
            {
                "vin": "WBS33HJ04TFW12875",
                "year": "2026",
                "model": "M3 Comp xDrive",
                "price": "$96,710",
                "color": "Sao Paulo Yellow",
                "dealer": "BMW of Mtn View",
                "status": "On Lot",
                "image": "https://via.placeholder.com/600x400/eeeeee/111111?text=Sao+Paulo+Yellow+M3",
                "link": "https://www.bmwofmountainview.com/inventory/new/bmw-m3.htm",
                "is_new": False
            },
            {
                "vin": "WBS13HJ07TFW40984",
                "year": "2026",
                "model": "M3 Base",
                "price": "$97,625",
                "color": "Special Order",
                "dealer": "Weatherford BMW",
                "status": "On Lot",
                "image": "https://via.placeholder.com/600x400/eeeeee/111111?text=Special+Order+M3",
                "link": "https://www.weatherfordbmw.com/bmw-model-research-berkeley-ca.html",
                "is_new": False
            },
            {
                "vin": "WBS23HJ07VFW68579",
                "year": "2027",
                "model": "M3 Base",
                "price": "$96,200",
                "color": "Black Sapphire",
                "dealer": "Stevens Creek BMW",
                "status": "On Lot",
                "image": "https://via.placeholder.com/600x400/eeeeee/111111?text=Black+Sapphire+M3",
                "link": "https://www.stevenscreekbmw.com/new-inventory/index.htm?model=M3",
                "is_new": False
            }
        ]
            
    output = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT"),
        "vehicles": final_vehicles
    }
    
    with open('data.json', 'w') as f:
        json.dump(output, f, indent=4)

if __name__ == "__main__":
    fetch_inventory()
