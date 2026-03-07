"""
JAL Points Flight Search – Flask web app.

Usage:
    cp .env.example .env          # add your seats.aero API key
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000
"""

import os
from datetime import date, datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import seats_aero

load_dotenv()

app = Flask(__name__)


def parse_date(value: str, fallback: date) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return fallback


@app.route("/")
def index():
    start_default, end_default = seats_aero.default_date_range()
    return render_template(
        "index.html",
        us_airports=seats_aero.US_AIRPORTS,
        japan_airports=seats_aero.JAPAN_AIRPORTS,
        cabin_labels=seats_aero.CABIN_LABELS,
        start_default=start_default.isoformat(),
        end_default=end_default.isoformat(),
    )


@app.route("/search")
def search():
    origins = request.args.getlist("origins") or list(seats_aero.US_AIRPORTS.keys())
    destinations = request.args.getlist("destinations") or list(seats_aero.JAPAN_AIRPORTS.keys())
    cabins = request.args.getlist("cabins") or ["J", "F"]

    start_default, end_default = seats_aero.default_date_range()
    start_date = parse_date(request.args.get("start_date"), start_default)
    end_date = parse_date(request.args.get("end_date"), end_default)

    # Clamp date range to 30 days max to avoid hammering the API
    max_end = start_date.replace(month=start_date.month) if False else start_date
    from datetime import timedelta
    if (end_date - start_date).days > 60:
        end_date = start_date + timedelta(days=60)

    error = None
    results = []
    try:
        results = seats_aero.search_availability(
            origins=origins,
            destinations=destinations,
            start_date=start_date,
            end_date=end_date,
            cabins=cabins,
        )
    except ValueError as e:
        error = str(e)
    except RuntimeError as e:
        error = str(e)

    return render_template(
        "results.html",
        results=results,
        error=error,
        us_airports=seats_aero.US_AIRPORTS,
        japan_airports=seats_aero.JAPAN_AIRPORTS,
        cabin_labels=seats_aero.CABIN_LABELS,
        origins=origins,
        destinations=destinations,
        cabins=cabins,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        start_default=start_default.isoformat(),
        end_default=end_default.isoformat(),
    )


@app.route("/api/search")
def api_search():
    """JSON endpoint for programmatic access."""
    origins = request.args.getlist("origins") or list(seats_aero.US_AIRPORTS.keys())
    destinations = request.args.getlist("destinations") or list(seats_aero.JAPAN_AIRPORTS.keys())
    cabins = request.args.getlist("cabins") or ["J", "F"]

    start_default, end_default = seats_aero.default_date_range()
    start_date = parse_date(request.args.get("start_date"), start_default)
    end_date = parse_date(request.args.get("end_date"), end_default)

    try:
        results = seats_aero.search_availability(
            origins=origins,
            destinations=destinations,
            start_date=start_date,
            end_date=end_date,
            cabins=cabins,
        )
        return jsonify({"ok": True, "count": len(results), "data": results})
    except (ValueError, RuntimeError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/trip/<availability_id>")
def api_trip(availability_id: str):
    """Return detailed flight segments for an availability entry."""
    try:
        trips = seats_aero.get_trip_details(availability_id)
        return jsonify({"ok": True, "data": trips})
    except RuntimeError as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
