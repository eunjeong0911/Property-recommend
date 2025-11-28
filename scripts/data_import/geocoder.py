import requests
import time
from config import Config

class Geocoder:
    @staticmethod
    def get_coordinates(address):
        """
        Get coordinates (lat, lng) for a given address using Kakao Local API.
        """
        if not Config.KAKAO_API_KEY:
            print("Error: KAKAO_API_KEY is not set in .env")
            return None, None

        url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {Config.KAKAO_API_KEY}"}
        params = {"query": address}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            if result["documents"]:
                document = result["documents"][0]
                # Kakao API returns y as latitude, x as longitude
                return float(document["y"]), float(document["x"])
            else:
                return None, None
        except Exception as e:
            print(f"Error geocoding address '{address}': {e}")
            return None, None
