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
STATION_NAME="Kylehaus Station" # Custom station name that will appear onscreen
```

Afterwards, just run `main.py`

<img width="1278" height="701" alt="merged_with_streetcar" src="https://github.com/user-attachments/assets/b184fe88-d582-4c9e-9273-ddd4ac329815" />

Times are displayed with the following color codes:
- White :white_large_square: means the vehicle is *on time*
- Green :green_square: means the vehicle is *early*
- Yellow :yellow_square: means the vehicle is *late (~2-5 minutes)*
- Red :red_square: means the vehicle is *very late (>5 minutes)*
- Grey 🔘 means that real-time tracking is temporarily unavailable for this vehicle

## Controls
There are two ways to exit the program, for setups with and without a keyboard:
- `Escape`
- `Right Click`

On the other hand, `Left Click` toggles fullscreen