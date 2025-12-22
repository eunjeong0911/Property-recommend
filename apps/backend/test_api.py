import os
import django
import sys
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from rest_framework.test import APIRequestFactory
from apps.listings.views import LandViewSet

def test_land_api():
    factory = APIRequestFactory()
    view = LandViewSet.as_view({'get': 'list'})

    # Test list endpoint
    request = factory.get('/api/listings/lands/')
    response = view(request)

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response Data (first item):")
        if len(response.data) > 0:
            print(response.data[0])
        else:
            print("No data found (empty list)")
    else:
        print("Error:", response.data)

if __name__ == "__main__":
    try:
        test_land_api()
    except Exception as e:
        print(f"Test failed: {e}")
