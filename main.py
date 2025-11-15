from dotenv import dotenv_values
import onebusaway
from datetime import datetime
import pytz

config = dotenv_values(".env")

API_KEY = config["API_KEY"]
REGION = config["REGION"]
BASE_URL = 'https://api.pugetsound.onebusaway.org/api/'
STOP_ID = "40_99610" # Cap Hill Station
time_zone = pytz.timezone(REGION)

# client = onebusaway.OneBusAwayClient(
#     api_key=YOUR_API_KEY,
#     base_url=BASE_URL
# )

print("Loaded API key")