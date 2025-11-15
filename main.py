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

client = onebusaway.OneBusAwayClient(
    api_key=API_KEY,
    base_url=BASE_URL
)

try:
    # Without any optional parameters, uses the API default time window
    response_data = client.get_arrivals_and_departures_for_stop(
        stop_id=STOP_ID
        # minutes_after=10
    )

    print(f"Successfully fetched {len(response_data.arrivalsAndDepartures)} arrivals/departures.")
    print(response_data)

except Exception as e:
    print(f"An error occurred: {e}")

print("Loaded API key")