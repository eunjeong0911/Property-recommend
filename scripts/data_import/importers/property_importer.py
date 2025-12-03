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
            # Fetch existing property IDs to skip redundant processing
            print("Fetching existing properties...")
            result = session.run("MATCH (p:Property) RETURN p.id AS id")
            existing_ids = {record["id"] for record in result}
            print(f"Found {len(existing_ids)} existing properties.")

            for json_file in json_files:
                file_path = os.path.join(data_dir, json_file)
                print(f"Processing {json_file}...")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    for item in data:
                        listing_id = item.get("매물번호")
                        
                        if not listing_id:
                            continue
                            
                        if listing_id in existing_ids:
                            continue

                        address_info = item.get("주소_정보", {})
                        full_address = address_info.get("전체주소")
                        
                        if not full_address:
                            continue

                        # Geocode address
                        lat, lng = Geocoder.get_coordinates(full_address)
                        
                        if lat is None or lng is None:
                            print(f"Skipping {listing_id}: Geocoding failed for {full_address}")
                            continue
                        
                        # Prepare properties
                        listing_info = item.get("매물_정보", {})
                        
                        # Extract name from various possible keys
                        name = listing_info.get("아파트명") or listing_info.get("건물명") or listing_info.get("오피스텔명") or "Unknown"

                        query = """
                        MERGE (p:Property {id: $id})
                        SET p.name = $name,
                            p.address = $address,
                            p.latitude = $latitude,
                            p.longitude = $longitude,
                            p.location = point({latitude: $latitude, longitude: $longitude})
                        """
                        
                        params = {
                            "id": listing_id,
                            "name": name,
                            "address": full_address,
                            "latitude": lat,
                            "longitude": lng
                        }

                        session.run(query, params)
                        time.sleep(0.1)

                except Exception as e:
                    print(f"Error processing file {json_file}: {e}")

if __name__ == "__main__":
    importer = PropertyImporter()
    importer.import_properties()
    Database.close()
