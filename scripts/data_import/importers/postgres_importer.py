import os
import json
import psycopg2
from psycopg2.extras import Json
from config import Config

class PostgresImporter:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        self.cur = self.conn.cursor()

    def import_properties(self):
        data_dir = os.path.join(Config.DATA_DIR, "home_data")
        if not os.path.exists(data_dir):
            print(f"Data directory not found: {data_dir}")
            return

        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        print(f"Found {len(json_files)} JSON files to process.")

        for json_file in json_files:
            file_path = os.path.join(data_dir, json_file)
            print(f"Processing {json_file}...")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for item in data:
                    self._insert_listing(item)
                
                self.conn.commit()
                print(f"Committed changes for {json_file}")

            except Exception as e:
                self.conn.rollback()
                print(f"Error processing file {json_file}: {e}")

    def _insert_listing(self, item):
        listing_id = item.get("매물번호")
        if not listing_id:
            return

        # Extract fields
        url = item.get("매물_URL")
        images = Json(item.get("매물_이미지", []))
        address_info = Json(item.get("주소_정보", {}))
        
        # Address extraction for the 'address' column (using full address)
        address = item.get("주소_정보", {}).get("전체주소")
        
        floor_plan_url = item.get("평면도_URL", [])
        trade_info = Json(item.get("거래_정보", {}))
        listing_info_data = item.get("매물_정보", {})
        listing_info = Json(listing_info_data)
        
        # Extract title/name for 'title' column
        title = listing_info_data.get("아파트명") or listing_info_data.get("건물명") or listing_info_data.get("오피스텔명") or "Unknown"

        additional_options = item.get("추가_옵션", [])
        nearby_schools = item.get("주변_학교", [])
        description = item.get("상세_설명")
        agent_info = Json(item.get("중개사_정보", {}))

        query = """
            INSERT INTO listings (
                listing_id, title, address, url, images, address_info, 
                floor_plan_url, trade_info, listing_info, additional_options, 
                nearby_schools, description, agent_info
            ) VALUES (
                %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, 
                %s, %s, %s
            )
            ON CONFLICT (listing_id) DO UPDATE SET
                title = EXCLUDED.title,
                address = EXCLUDED.address,
                url = EXCLUDED.url,
                images = EXCLUDED.images,
                address_info = EXCLUDED.address_info,
                floor_plan_url = EXCLUDED.floor_plan_url,
                trade_info = EXCLUDED.trade_info,
                listing_info = EXCLUDED.listing_info,
                additional_options = EXCLUDED.additional_options,
                nearby_schools = EXCLUDED.nearby_schools,
                description = EXCLUDED.description,
                agent_info = EXCLUDED.agent_info,
                updated_at = CURRENT_TIMESTAMP;
        """

        self.cur.execute(query, (
            listing_id, title, address, url, images, address_info,
            floor_plan_url, trade_info, listing_info, additional_options,
            nearby_schools, description, agent_info
        ))

    def close(self):
        self.cur.close()
        self.conn.close()

if __name__ == "__main__":
    importer = PostgresImporter()
    try:
        importer.import_properties()
    finally:
        importer.close()
