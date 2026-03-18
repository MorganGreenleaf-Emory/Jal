"""
JAL Points Flight Search – Flask web app.

Usage:
    cp .env.example .env          # add your seats.aero API key
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000
"""

import os
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import seats_aero
import zipair as zipair_mod

load_dotenv()

app = Flask(__name__)

# Hardcoded trip dates for the ATL→Tokyo trip
ATL_TOKYO_OUTBOUND = date(2026, 5, 24)
ATL_TOKYO_RETURN = date(2026, 6, 9)
ATL_TOKYO_DESTINATIONS = ["HND", "NRT"]


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


# ---------------------------------------------------------------------------
# ATL → Tokyo specialized routes
# ---------------------------------------------------------------------------

@app.route("/atl-tokyo")
def atl_tokyo():
    """Landing page for the ATL→Tokyo May 24–June 9 trip finder."""
    outbound_date = parse_date(request.args.get("outbound_date"), ATL_TOKYO_OUTBOUND)
    return_date = parse_date(request.args.get("return_date"), ATL_TOKYO_RETURN)
    return render_template(
        "atl_tokyo.html",
        outbound_date=outbound_date.isoformat(),
        return_date=return_date.isoformat(),
        cabin_labels=seats_aero.CABIN_LABELS,
        atl_gateways=seats_aero.ATL_GATEWAYS,
        atl_connection_quality=seats_aero.ATL_CONNECTION_QUALITY,
        zipair_cabins=zipair_mod.ZIPAIR_CABINS,
    )


@app.route("/atl-tokyo/search")
def atl_tokyo_search():
    """
    Search JAL award availability for the ATL→Tokyo trip.

    Searches all ATL-friendly gateways for both outbound and return legs,
    scores each result, and returns the ranked list alongside Zipair options.
    """
    outbound_date = parse_date(request.args.get("outbound_date"), ATL_TOKYO_OUTBOUND)
    return_date = parse_date(request.args.get("return_date"), ATL_TOKYO_RETURN)
    cabins = request.args.getlist("cabins") or ["Y", "W", "J", "F"]
    gateways = list(seats_aero.ATL_GATEWAYS.keys())

    outbound_results, outbound_error = [], None
    return_results, return_error = [], None

    try:
        outbound_results = seats_aero.search_availability(
            origins=gateways,
            destinations=ATL_TOKYO_DESTINATIONS,
            start_date=outbound_date,
            end_date=outbound_date + timedelta(days=2),
            cabins=cabins,
        )
        # Attach value scores
        for r in outbound_results:
            r["value_score"] = seats_aero.value_score(r)
            conn = seats_aero.ATL_CONNECTION_QUALITY.get(r["origin"])
            if conn:
                r["conn_score"], r["conn_dots"], r["conn_desc"] = conn
        outbound_results.sort(key=lambda r: r["value_score"], reverse=True)
    except (ValueError, RuntimeError) as e:
        outbound_error = str(e)

    try:
        return_results = seats_aero.search_availability(
            origins=ATL_TOKYO_DESTINATIONS,
            destinations=gateways,
            start_date=return_date,
            end_date=return_date + timedelta(days=2),
            cabins=cabins,
        )
        for r in return_results:
            r["value_score"] = seats_aero.value_score(r)
            conn = seats_aero.ATL_CONNECTION_QUALITY.get(r["destination"])
            if conn:
                r["conn_score"], r["conn_dots"], r["conn_desc"] = conn
        return_results.sort(key=lambda r: r["value_score"], reverse=True)
    except (ValueError, RuntimeError) as e:
        return_error = str(e)

    # Zipair options
    zipair_outbound = zipair_mod.get_outbound_options(outbound_date)
    zipair_return = zipair_mod.get_return_options(return_date)

    # Best pick: highest scored result across both legs
    best_pick = None
    if outbound_results:
        best_pick = {"direction": "outbound", "result": outbound_results[0]}

    return render_template(
        "atl_tokyo_results.html",
        outbound_date=outbound_date.isoformat(),
        return_date=return_date.isoformat(),
        outbound_results=outbound_results,
        return_results=return_results,
        outbound_error=outbound_error,
        return_error=return_error,
        zipair_outbound=zipair_outbound,
        zipair_return=zipair_return,
        zipair_cabins=zipair_mod.ZIPAIR_CABINS,
        cabin_labels=seats_aero.CABIN_LABELS,
        atl_gateways=seats_aero.ATL_GATEWAYS,
        atl_connection_quality=seats_aero.ATL_CONNECTION_QUALITY,
        best_pick=best_pick,
        cabins=cabins,
    )


@app.route("/api/atl-tokyo/search")
def api_atl_tokyo_search():
    """JSON endpoint for the ATL→Tokyo search."""
    outbound_date = parse_date(request.args.get("outbound_date"), ATL_TOKYO_OUTBOUND)
    return_date = parse_date(request.args.get("return_date"), ATL_TOKYO_RETURN)
    cabins = request.args.getlist("cabins") or ["Y", "W", "J", "F"]
    gateways = list(seats_aero.ATL_GATEWAYS.keys())

    try:
        outbound = seats_aero.search_availability(
            origins=gateways,
            destinations=ATL_TOKYO_DESTINATIONS,
            start_date=outbound_date,
            end_date=outbound_date + timedelta(days=2),
            cabins=cabins,
        )
        for r in outbound:
            r["value_score"] = seats_aero.value_score(r)
        outbound.sort(key=lambda r: r["value_score"], reverse=True)

        ret = seats_aero.search_availability(
            origins=ATL_TOKYO_DESTINATIONS,
            destinations=gateways,
            start_date=return_date,
            end_date=return_date + timedelta(days=2),
            cabins=cabins,
        )
        for r in ret:
            r["value_score"] = seats_aero.value_score(r)
        ret.sort(key=lambda r: r["value_score"], reverse=True)

        return jsonify({
            "ok": True,
            "outbound_count": len(outbound),
            "return_count": len(ret),
            "outbound": outbound,
            "return": ret,
            "zipair_outbound": zipair_mod.get_outbound_options(outbound_date),
            "zipair_return": zipair_mod.get_return_options(return_date),
        })
    except (ValueError, RuntimeError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
