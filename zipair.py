"""
Zipair route data and booking link generator.

Zipair is a JAL subsidiary low-cost carrier flying from Tokyo Narita (NRT)
to select US cities. No public API – this module provides static route data
and generates deep links to the Zipair booking engine.

Zipair cabin classes:
  ECO        – Economy (basic seat, carry-on only)
  ECO_PLUS   – Economy Plus (more legroom, carry-on + checked bag)
  FULL_FLAT  – Full-flat business-style seat (lie-flat, meal, lounge)
"""

from datetime import date

# ---------------------------------------------------------------------------
# Route catalogue
# ---------------------------------------------------------------------------

# Each entry: origin, destination, flight_time_hrs, notes
ZIPAIR_US_ROUTES = [
    {
        "origin": "NRT",
        "destination": "LAX",
        "origin_name": "Tokyo Narita",
        "dest_name": "Los Angeles (LAX)",
        "flight_time_hrs": 10.5,
        "frequency": "Daily",
        "cabins": ["ECO", "ECO_PLUS", "FULL_FLAT"],
        "atl_connection": {
            "airport": "LAX",
            "typical_flight_time": "4h 30m",
            "typical_carriers": ["Delta", "American", "United"],
            "connection_quality": 3,  # 1-3 scale
        },
    },
    {
        "origin": "NRT",
        "destination": "SFO",
        "origin_name": "Tokyo Narita",
        "dest_name": "San Francisco (SFO)",
        "flight_time_hrs": 10.0,
        "frequency": "Daily",
        "cabins": ["ECO", "ECO_PLUS", "FULL_FLAT"],
        "atl_connection": {
            "airport": "SFO",
            "typical_flight_time": "5h 00m",
            "typical_carriers": ["Delta", "United"],
            "connection_quality": 2,
        },
    },
    {
        "origin": "NRT",
        "destination": "IAH",
        "origin_name": "Tokyo Narita",
        "dest_name": "Houston (IAH)",
        "flight_time_hrs": 13.5,
        "frequency": "Select days",
        "cabins": ["ECO", "ECO_PLUS"],
        "atl_connection": {
            "airport": "IAH",
            "typical_flight_time": "2h 15m",
            "typical_carriers": ["Delta", "United"],
            "connection_quality": 3,
        },
    },
]

# Reverse routes (ATL → Tokyo outbound via Zipair US gateways)
ZIPAIR_US_ROUTES_OUTBOUND = [
    {
        "origin": "LAX",
        "destination": "NRT",
        "origin_name": "Los Angeles (LAX)",
        "dest_name": "Tokyo Narita",
        "flight_time_hrs": 11.5,
        "frequency": "Daily",
        "cabins": ["ECO", "ECO_PLUS", "FULL_FLAT"],
        "atl_connection": {
            "airport": "LAX",
            "typical_flight_time": "4h 30m",
            "typical_carriers": ["Delta", "American", "United"],
            "connection_quality": 3,
        },
    },
    {
        "origin": "SFO",
        "destination": "NRT",
        "origin_name": "San Francisco (SFO)",
        "dest_name": "Tokyo Narita",
        "flight_time_hrs": 11.0,
        "frequency": "Daily",
        "cabins": ["ECO", "ECO_PLUS", "FULL_FLAT"],
        "atl_connection": {
            "airport": "SFO",
            "typical_flight_time": "5h 00m",
            "typical_carriers": ["Delta", "United"],
            "connection_quality": 2,
        },
    },
    {
        "origin": "IAH",
        "destination": "NRT",
        "origin_name": "Houston (IAH)",
        "dest_name": "Tokyo Narita",
        "flight_time_hrs": 14.5,
        "frequency": "Select days",
        "cabins": ["ECO", "ECO_PLUS"],
        "atl_connection": {
            "airport": "IAH",
            "typical_flight_time": "2h 15m",
            "typical_carriers": ["Delta", "United"],
            "connection_quality": 3,
        },
    },
]

# ---------------------------------------------------------------------------
# Cabin metadata
# ---------------------------------------------------------------------------

ZIPAIR_CABINS = {
    "ECO": {
        "label": "Economy",
        "short": "Eco",
        "description": "Standard seat, personal device entertainment, carry-on included.",
        "price_range": "$400–$650",
        "seat_type": "Recline",
        "baggage": "Carry-on only",
        "color_class": "zipair-eco",
    },
    "ECO_PLUS": {
        "label": "Economy Plus",
        "short": "Eco+",
        "description": "Extra legroom, priority boarding, 1 checked bag included.",
        "price_range": "$650–$950",
        "seat_type": "Recline (extra pitch)",
        "baggage": "1 checked bag",
        "color_class": "zipair-ecoplus",
    },
    "FULL_FLAT": {
        "label": "Full-flat",
        "short": "Flat",
        "description": "Lie-flat business-class seat, premium meal, lounge access.",
        "price_range": "$1,200–$1,900",
        "seat_type": "Lie-flat",
        "baggage": "2 checked bags",
        "color_class": "zipair-flat",
    },
}

CONNECTION_QUALITY_LABELS = {
    1: ("●○○", "Limited service from ATL"),
    2: ("●●○", "Good ATL connections"),
    3: ("●●●", "Frequent ATL connections"),
}

# ---------------------------------------------------------------------------
# Booking URL generation
# ---------------------------------------------------------------------------

ZIPAIR_SEARCH_BASE = "https://www.zipair.net/en/flight/search"


def booking_url(origin: str, destination: str, departure_date: date, adults: int = 1) -> str:
    """Generate a Zipair deep link for a specific route and date."""
    date_str = departure_date.strftime("%Y%m%d")
    return (
        f"{ZIPAIR_SEARCH_BASE}"
        f"?origin={origin}&destination={destination}"
        f"&departureDate={date_str}&adults={adults}"
    )


def get_outbound_options(departure_date: date) -> list[dict]:
    """Return Zipair outbound options (ATL→Tokyo via gateway) with booking links."""
    options = []
    for route in ZIPAIR_US_ROUTES_OUTBOUND:
        option = dict(route)
        option["booking_url"] = booking_url(route["origin"], route["destination"], departure_date)
        option["departure_date"] = departure_date.isoformat()
        option["direction"] = "outbound"
        options.append(option)
    return options


def get_return_options(departure_date: date) -> list[dict]:
    """Return Zipair return options (Tokyo→ATL via gateway) with booking links."""
    options = []
    for route in ZIPAIR_US_ROUTES:
        option = dict(route)
        option["booking_url"] = booking_url(route["origin"], route["destination"], departure_date)
        option["departure_date"] = departure_date.isoformat()
        option["direction"] = "return"
        options.append(option)
    return options
