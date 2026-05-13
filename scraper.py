import json
import requests
from datetime import datetime

# Targeting common dealer platform JSON endpoints
DEALERS = [
    {"name": "East Bay BMW", "url": "https://www.eastbaybmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3"},
    {"name": "Weatherford BMW", "url": "https://www.weatherfordbmw.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory?make=BMW&model=M3"}
]

def fetch_inventory():
    vehicles = []
    
    for dealer in DEALERS:
        try:
            # We spoof a standard browser to prevent immediate blocking
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            response = requests.get(dealer['url'], headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'pageInfo' in data and 'trackingData' in data['pageInfo']:
                    for car in data['pageInfo']['trackingData']:
                        if 'M3' in car.get('model', ''):
                            vehicles.append({
                                "vin": car.get('vin', 'N/A'),
                                "year": car.get('modelYear', '2024'),
                                "model": "M3 Competition" if 'Comp' in car.get('trim', '') else "M3",
                                "price": f"${car.get('askingPrice', 'Call')}",
                                "color": car.get('exteriorColor', 'Unknown'),
                                "dealer": dealer['name'],
                                "status": "In Transit" if car.get('inTransit') else "On Lot",
                                "image": car.get('imageURL', 'https://via.placeholder.com/600x400?text=Image+Unavailable'),
                                "link": f"https://www.{dealer['name'].replace(' ', '').lower()}.com/new/{car.get('vin')}.htm",
                                "is_new": True 
                            })
        except Exception as e:
            print(f"Connection skipped for {dealer['name']}")
            
    # Compile and save to a local JSON file
    output = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S PDT"),
        "vehicles": vehicles
    }
    
    with open('data.json', 'w') as f:
        json.dump(output, f, indent=4)

if __name__ == "__main__":
    fetch_inventory()
