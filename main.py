from dotenv import dotenv_values
import onebusaway
from datetime import datetime
import pytz

config = dotenv_values(".env")

API_KEY = config["API_KEY"]
BASE_URL = config["BASE_URL"]
STOP_ID = "40_99610" # Cap Hill Station
time_zone = pytz.timezone('America/Los_Angeles')

# client = onebusaway.OneBusAwayClient(
#     api_key=YOUR_API_KEY,
#     base_url=BASE_URL
# )

print("Loaded API key")