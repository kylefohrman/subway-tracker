# subway-tracker
Lightweight Metro Arrivals Board for the Seattle Subway, integrated with OneBusAway API

## Usage instructions
On a fresh raspberry pi, you might need the following packages:
```
pip install onebusaway
pip install dotenv
pip install pytz
pip install pygame
```

You will also need a `.env` file, where you will store private data:
```
API_KEY=[Your API Key from OneBusAway]
REGION="America/Los_Angeles"
STATION_NAME="Kylehaus Station"
```

Afterwards, just run `main.py`
