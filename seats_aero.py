"""
seats.aero API client for JAL award flight search.

API docs: https://developers.seats.aero/
Auth: Partner-Authorization header (Pro subscription required)
"""

import os
import requests
from datetime import date, timedelta

BASE_URL = "https://seats.aero/partnerapi"

# JAL-operated US gateways with direct service to Japan
US_AIRPORTS = {
    "JFK": "New York (JFK)",
    "LAX": "Los Angeles (LAX)",
    "SFO": "San Francisco (SFO)",
    "ORD": "Chicago (ORD)",
    "DFW": "Dallas-Fort Worth (DFW)",
    "BOS": "Boston (BOS)",
    "SEA": "Seattle (SEA)",
    "HNL": "Honolulu (HNL)",
}

# Japan airports served by JAL
JAPAN_AIRPORTS = {
    "HND": "Tokyo Haneda (HND)",
    "NRT": "Tokyo Narita (NRT)",
    "KIX": "Osaka Kansai (KIX)",
    "NGO": "Nagoya (NGO)",
    "CTS": "Sapporo (CTS)",
    "FUK": "Fukuoka (FUK)",
    "OKA": "Okinawa (OKA)",
}

CABIN_LABELS = {
    "Y": "Economy",
    "W": "Premium Economy",
    "J": "Business",
    "F": "First",
}


def _get_api_key() -> str:
    key = os.environ.get("SEATS_AERO_API_KEY", "")
    if not key or key == "your_api_key_here":
        raise ValueError("SEATS_AERO_API_KEY is not set. Copy .env.example to .env and add your key.")
    return key


def _headers() -> dict:
    return {
        "Partner-Authorization": _get_api_key(),
        "Accept": "application/json",
    }


def search_availability(
    origins: list[str],
    destinations: list[str],
    start_date: date,
    end_date: date,
    cabins: list[str],
) -> list[dict]:
    """
    Search JAL award availability via seats.aero bulk availability endpoint.

    Returns a list of result dicts, one per available origin/destination/date/cabin.
    """
    results = []
    session = requests.Session()
    session.headers.update(_headers())

    for origin in origins:
        for destination in destinations:
            params = {
                "source": "jal",
                "origin": origin,
                "destination": destination,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
            try:
                resp = session.get(f"{BASE_URL}/availability", params=params, timeout=20)
                resp.raise_for_status()
                data = resp.json().get("data") or []
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 401:
                    raise ValueError("Invalid API key. Check your SEATS_AERO_API_KEY.") from e
                raise
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"Network error querying seats.aero: {e}") from e

            for entry in data:
                for cabin_code in cabins:
                    avail_key = f"{cabin_code}Available"
                    miles_key = f"{cabin_code}MileageCost"
                    remaining_key = f"{cabin_code}RemainingSeats"

                    if entry.get(avail_key):
                        results.append({
                            "origin": entry.get("OriginAirport", origin),
                            "destination": entry.get("DestinationAirport", destination),
                            "date": entry.get("Date", ""),
                            "cabin_code": cabin_code,
                            "cabin": CABIN_LABELS.get(cabin_code, cabin_code),
                            "miles": entry.get(miles_key),
                            "remaining_seats": entry.get(remaining_key),
                            "availability_id": entry.get("ID"),
                            "source": "JAL Mileage Bank",
                        })

    results.sort(key=lambda r: (r["date"], r["origin"], r["destination"], r["cabin_code"]))
    return results


def get_trip_details(availability_id: str) -> list[dict]:
    """Fetch detailed flight segments for an availability entry."""
    session = requests.Session()
    session.headers.update(_headers())
    try:
        resp = session.get(f"{BASE_URL}/trips", params={"id": availability_id}, timeout=20)
        resp.raise_for_status()
        return resp.json().get("data") or []
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error fetching trip details: {e}") from e


def default_date_range() -> tuple[date, date]:
    today = date.today()
    return today + timedelta(days=1), today + timedelta(days=30)
