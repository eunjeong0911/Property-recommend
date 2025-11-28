import os
import json
import time
from config import Config
from database import Database
from geocoder import Geocoder

class PropertyImporter:
    def __init__(self):
        self.driver = Database.get_driver()

    def import_properties(self):
        data_dir = os.path.join(Config.DATA_DIR, "home_data")
        if not os.path.exists(data_dir):
            print(f"Data directory not found: {data_dir}")
            return

        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        print(f"Found {len(json_files)} JSON files to process.")

        with self.driver.session() as session:
            for json_file in json_files:
                file_path = os.path.join(data_dir, json_file)
                print(f"Processing {json_file}...")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    for item in data:
                        listing_id = item.get("매물번호")
                        address_info = item.get("주소_정보", {})
                        full_address = address_info.get("전체주소")
                        
                        if not listing_id or not full_address:
                            continue

                        # Geocode address
                        lat, lng = Geocoder.get_coordinates(full_address)
                        
                        # Prepare properties
                        trade_info = item.get("거래_정보", {})
                        listing_info = item.get("매물_정보", {})
                        trade_type_raw = trade_info.get("거래방식", "")
                        bldg_type = listing_info.get("건물형태", "Unknown")

                        query = """
                        MERGE (p:Property {id: $id})
                        SET p.address = $address,
                            p.latitude = $latitude,
                            p.longitude = $longitude,
                            p.location = point({latitude: $latitude, longitude: $longitude}),
                            p.bldg_type = $bldg_type,
                            p.trade_type_raw = $trade_type_raw,
                            p.updated_at = datetime()
                        """
                        
                        params = {
                            "id": listing_id,
                            "address": full_address,
                            "latitude": lat,
                            "longitude": lng,
                            "bldg_type": bldg_type,
                            "trade_type_raw": trade_type_raw
                        }

                        session.run(query, params)
                        time.sleep(0.1)

                except Exception as e:
                    print(f"Error processing file {json_file}: {e}")

if __name__ == "__main__":
    importer = PropertyImporter()
    importer.import_properties()
    Database.close()
