# alchPRO/services/api.py
import requests
from config import API_BASE_URL, API_HEADERS

class WikiAPI:
    @staticmethod
    def fetch_all_data():
        """Fetches mapping, latest prices, 1h volumes, and current nature rune cost."""
        mapping_data = []
        prices_data = {}
        volume_data = {}
        nature_rune_cost = 90

        try:
            # 1. Mapping
            map_res = requests.get(f"{API_BASE_URL}/mapping", headers=API_HEADERS, timeout=10)
            if map_res.status_code == 200:
                mapping_data = map_res.json()

            # 2. Latest Prices
            latest_res = requests.get(f"{API_BASE_URL}/latest", headers=API_HEADERS, timeout=10)
            if latest_res.status_code == 200:
                prices_data = latest_res.json().get('data', {})

            # 3. Hourly Volumes
            hourly_res = requests.get(f"{API_BASE_URL}/1h", headers=API_HEADERS, timeout=10)
            if hourly_res.status_code == 200:
                volume_data = hourly_res.json().get('data', {})

            # Extract nature rune price (ID: 561)
            nature_api = prices_data.get("561")
            if nature_api and nature_api.get('high'):
                nature_rune_cost = int(nature_api.get('high'))

            return True, mapping_data, prices_data, volume_data, nature_rune_cost

        except Exception as err:
            return False, str(err), {}, {}, 90# alchPRO/services/api.py
import requests
from config import API_BASE_URL, API_HEADERS

class WikiAPI:
    @staticmethod
    def fetch_all_data():
        """Fetches mapping, latest prices, 1h volumes, and current nature rune cost."""
        mapping_data = []
        prices_data = {}
        volume_data = {}
        nature_rune_cost = 90

        try:
            # 1. Mapping
            map_res = requests.get(f"{API_BASE_URL}/mapping", headers=API_HEADERS, timeout=10)
            if map_res.status_code == 200:
                mapping_data = map_res.json()

            # 2. Latest Prices
            latest_res = requests.get(f"{API_BASE_URL}/latest", headers=API_HEADERS, timeout=10)
            if latest_res.status_code == 200:
                prices_data = latest_res.json().get('data', {})

            # 3. Hourly Volumes
            hourly_res = requests.get(f"{API_BASE_URL}/1h", headers=API_HEADERS, timeout=10)
            if hourly_res.status_code == 200:
                volume_data = hourly_res.json().get('data', {})

            # Extract nature rune price (ID: 561)
            nature_api = prices_data.get("561")
            if nature_api and nature_api.get('high'):
                nature_rune_cost = int(nature_api.get('high'))

            return True, mapping_data, prices_data, volume_data, nature_rune_cost

        except Exception as err:
            return False, str(err), {}, {}, 90