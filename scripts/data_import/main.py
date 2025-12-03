import sys
import os

# Add scripts/data_import to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from importers.transport_importer import TransportImporter
from importers.amenity_importer import AmenityImporter
from importers.safety_importer import SafetyImporter
from importers.property_importer import PropertyImporter
from importers.postgres_importer import PostgresImporter
from database import Database

def main():
    print("Starting Data Import Pipeline...")
    
    # 1. Transport
    print("\n--- Importing Transport Data ---")
    transport = TransportImporter()
    transport.import_subway()
    transport.import_bus()
    
    # 2. Amenity
    print("\n--- Importing Amenity Data ---")
    amenity = AmenityImporter()
    amenity.import_medical()
    amenity.import_college()
    amenity.import_store()
    amenity.import_park()
    
    # 3. Safety & Office
    print("\n--- Importing Safety & Office Data ---")
    safety = SafetyImporter()
    safety.import_cctv()
    safety.import_bell()
    safety.import_police()
    safety.import_fire()
    
    # 4. Property (Home)
    print("\n--- Importing Property Data (Neo4j) ---")
    prop = PropertyImporter()
    prop.import_properties()

    # 5. Property (Postgres)
    print("\n--- Importing Property Data (PostgreSQL) ---")
    pg_importer = PostgresImporter()
    try:
        pg_importer.import_properties()
    finally:
        pg_importer.close()

    # 6. Linking Data (Must be done after Property import)
    print("\n--- Linking Data ---")
    
    # Transport Linking
    transport.link_subway()
    transport.link_bus()
    
    # Amenity Linking
    amenity.link_hospital()
    amenity.link_pharmacy()
    amenity.link_college()
    amenity.link_convenience()
    amenity.link_park()
    
    # Safety Linking
    safety.link_cctv()
    safety.link_bell()
    safety.link_police()
    safety.link_fire()
    
    Database.close()
    print("\nData Import Pipeline Completed Successfully!")

if __name__ == "__main__":
    main()
