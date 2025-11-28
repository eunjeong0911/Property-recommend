import sys
import os

# Add scripts/data_import to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from importers.transport_importer import TransportImporter
from importers.amenity_importer import AmenityImporter
from importers.safety_importer import SafetyImporter
from importers.property_importer import PropertyImporter
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
    # Note: Property import relies on geocoding which can be slow and rate-limited.
    # It might be better to run this separately or last.
    print("\n--- Importing Property Data ---")
    prop = PropertyImporter()
    prop.import_properties()
    
    Database.close()
    print("\nData Import Pipeline Completed Successfully!")

if __name__ == "__main__":
    main()
