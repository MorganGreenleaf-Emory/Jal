# JAL Points Flight Search

A web app that systematically searches for award seat availability on US → Japan flights using JAL Mileage Bank points, powered by the [seats.aero](https://seats.aero) API.

## Features

- Search all major US gateways (JFK, LAX, SFO, ORD, DFW, BOS, SEA, HNL)
- Search all major Japan airports (HND, NRT, KIX, NGO, CTS, FUK, OKA)
- Filter by cabin class: Economy, Premium Economy, Business, First
- Flexible date range picker (up to 60 days per search)
- Results table with mileage cost and seat counts
- JSON API endpoint for scripting or further automation

## Prerequisites

- Python 3.10+
- A [seats.aero Pro](https://seats.aero) subscription (~$10/month) for API access

## Setup

1. **Clone the repo and install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your API key**

   ```bash
   cp .env.example .env
   ```

   Open `.env` and replace `your_api_key_here` with your seats.aero API key.
   Get your key at: https://seats.aero/account/api

3. **Run the app**

   ```bash
   python app.py
   ```

   Open your browser at [http://localhost:5000](http://localhost:5000).

## Usage

### Web interface

1. Select one or more **origin airports** in the US.
2. Select one or more **destination airports** in Japan.
3. Set a **date range** (up to 60 days).
4. Choose **cabin classes** to include.
5. Click **Search Award Availability**.

Results are sorted by date and show the mileage cost, remaining seats, and a link to book on JAL.co.jp.

### JSON API

```bash
# Search business and first class, LAX→HND, next 30 days
curl "http://localhost:5000/api/search?origins=LAX&destinations=HND&cabins=J&cabins=F&start_date=2026-03-09&end_date=2026-04-08"
```

Response:
```json
{
  "ok": true,
  "count": 4,
  "data": [
    {
      "origin": "LAX",
      "destination": "HND",
      "date": "2026-03-12",
      "cabin_code": "J",
      "cabin": "Business",
      "miles": 60000,
      "remaining_seats": 2,
      "availability_id": "...",
      "source": "JAL Mileage Bank"
    }
  ]
}
```

**Available query parameters**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `origins` | US airport code(s) | `LAX`, `JFK` |
| `destinations` | Japan airport code(s) | `HND`, `NRT` |
| `cabins` | Cabin code(s): `Y` `W` `J` `F` | `J`, `F` |
| `start_date` | Start date (YYYY-MM-DD) | `2026-03-09` |
| `end_date` | End date (YYYY-MM-DD) | `2026-04-08` |

Multiple values for the same parameter are supported (e.g. `?origins=LAX&origins=JFK`).

## Project structure

```
.
├── app.py           # Flask routes (web UI + JSON API)
├── seats_aero.py    # seats.aero API client
├── requirements.txt
├── .env.example     # Copy to .env and add your API key
├── templates/
│   ├── base.html
│   ├── index.html   # Search form
│   └── results.html # Results table
└── static/
    └── style.css
```

## Notes

- Award data from seats.aero is **cached**, not real-time. Always confirm availability on [JAL.co.jp](https://www.jal.co.jp/jp/en/jalmile/use/jal/inter/application.html) before booking.
- JAL releases award seats up to **360 days** in advance.
- Business and First class seats are limited. Searching broadly (multiple airports, wider date ranges) improves your chances.
- Approximate one-way mileage costs: Economy ~30k, Premium Economy ~43k, Business ~50k–60k, First ~80k miles.
