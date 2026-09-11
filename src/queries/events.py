"""
Consultas de eventos a Mixpanel API.

Funcionalidades:
- Conteo de eventos por nombre y rango de fechas (1.1)
- Usuarios unicos por evento (1.3)
- Colegios unicos por evento (1.4)
- CLI basico (1.6)

Uso CLI:
    python -m src.queries.events --event "FUR Speech Import Completed" --days 7
    python -m src.queries.events --event "Page View" --from 2026-09-01 --to 2026-09-07
"""

import argparse
import json
import logging
from datetime import date, timedelta

from src.client import MixpanelClient

logger = logging.getLogger(__name__)

# Ciudades conocidas de bots (del config/features.json)
BOT_CITIES = {"Dulles", "Cheyenne", "Chicago", "Phoenix", "Des Moines", "Boydton", "San Jose"}


def _resolve_dates(from_date: str | None, to_date: str | None, days: int | None) -> tuple[str, str]:
    """Resuelve fechas de inicio/fin a partir de parametros CLI."""
    today = date.today()
    if from_date and to_date:
        return from_date, to_date
    if days:
        return (today - timedelta(days=days)).isoformat(), today.isoformat()
    # Default: ultimos 7 dias
    return (today - timedelta(days=7)).isoformat(), today.isoformat()


def count_events(
    client: MixpanelClient,
    event: str,
    from_date: str,
    to_date: str,
    where: str | None = None,
) -> dict:
    """
    Cuenta eventos por dia para un evento dado.

    Returns:
        {
            "event": "FUR Speech Import Completed",
            "from_date": "2026-09-01",
            "to_date": "2026-09-07",
            "by_date": {"2026-09-01": 5, "2026-09-02": 3, ...},
            "total": 42
        }
    """
    result = client.segmentation(
        event=event,
        from_date=from_date,
        to_date=to_date,
        where=where,
    )

    values = result.get("data", {}).get("values", {})
    # La API retorna: {"values": {"EventName": {"2026-09-01": 5, ...}}}
    by_date = values.get(event, {})
    total = sum(by_date.values())

    return {
        "event": event,
        "from_date": from_date,
        "to_date": to_date,
        "by_date": by_date,
        "total": total,
    }


def count_unique_users(
    client: MixpanelClient,
    event: str,
    from_date: str,
    to_date: str,
    where: str | None = None,
) -> dict:
    """
    Cuenta usuarios unicos (distinct_id) via raw export.

    Returns:
        {
            "event": "...",
            "unique_users": 15,
            "user_ids": ["u1", "u2", ...],
            "from_date": "...",
            "to_date": "..."
        }
    """
    events = client.export(
        from_date=from_date,
        to_date=to_date,
        event=event,
        where=where,
    )

    # Filtrar bots por ciudad
    real_events = [
        e for e in events
        if e.get("properties", {}).get("$city") not in BOT_CITIES
    ]

    user_ids = {
        e.get("properties", {}).get("distinct_id")
        for e in real_events
        if e.get("properties", {}).get("distinct_id")
    }

    return {
        "event": event,
        "from_date": from_date,
        "to_date": to_date,
        "unique_users": len(user_ids),
        "user_ids": sorted(user_ids),
        "total_events": len(real_events),
        "bot_events_filtered": len(events) - len(real_events),
    }


def count_unique_schools(
    client: MixpanelClient,
    event: str,
    from_date: str,
    to_date: str,
    rbd_property: str = "rbd",
    where: str | None = None,
) -> dict:
    """
    Cuenta colegios unicos (por RBD) via raw export.

    Returns:
        {
            "event": "...",
            "unique_schools": 8,
            "rbds": ["12345", "67890", ...],
            "from_date": "...",
            "to_date": "..."
        }
    """
    events = client.export(
        from_date=from_date,
        to_date=to_date,
        event=event,
        where=where,
    )

    # Filtrar bots
    real_events = [
        e for e in events
        if e.get("properties", {}).get("$city") not in BOT_CITIES
    ]

    rbds = {
        str(e.get("properties", {}).get(rbd_property))
        for e in real_events
        if e.get("properties", {}).get(rbd_property)
    }

    return {
        "event": event,
        "from_date": from_date,
        "to_date": to_date,
        "unique_schools": len(rbds),
        "rbds": sorted(rbds),
    }


def full_event_summary(
    client: MixpanelClient,
    event: str,
    from_date: str,
    to_date: str,
    where: str | None = None,
) -> dict:
    """Resumen completo: conteo + usuarios unicos + colegios unicos."""
    events_raw = client.export(
        from_date=from_date,
        to_date=to_date,
        event=event,
        where=where,
    )

    # Filtrar bots
    real_events = [
        e for e in events_raw
        if e.get("properties", {}).get("$city") not in BOT_CITIES
    ]

    user_ids = set()
    rbds = set()
    by_date: dict[str, int] = {}

    for e in real_events:
        props = e.get("properties", {})

        did = props.get("distinct_id")
        if did:
            user_ids.add(did)

        rbd = props.get("rbd")
        if rbd:
            rbds.add(str(rbd))

        # Agrupar por fecha
        ts = props.get("time")
        if ts:
            from datetime import datetime
            day = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            by_date[day] = by_date.get(day, 0) + 1

    return {
        "event": event,
        "from_date": from_date,
        "to_date": to_date,
        "total_events": len(real_events),
        "bot_events_filtered": len(events_raw) - len(real_events),
        "unique_users": len(user_ids),
        "unique_schools": len(rbds),
        "by_date": dict(sorted(by_date.items())),
    }


# --- CLI ---

def _print_table(summary: dict) -> None:
    """Imprime un resumen formateado en consola."""
    print("=" * 60)
    print(f"CONSULTA DE EVENTOS — {summary['event']}")
    print("=" * 60)
    print(f"  Periodo:          {summary['from_date']} → {summary['to_date']}")
    print(f"  Eventos totales:  {summary['total_events']}")
    print(f"  Bots filtrados:   {summary['bot_events_filtered']}")
    print(f"  Usuarios unicos:  {summary['unique_users']}")
    print(f"  Colegios unicos:  {summary['unique_schools']}")

    if summary.get("by_date"):
        print()
        print("  DETALLE POR DIA")
        print("  " + "-" * 40)
        for day, count in summary["by_date"].items():
            print(f"  {day}    {count:>6} eventos")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Consultar eventos de Mixpanel",
        prog="python -m src.queries.events",
    )
    parser.add_argument(
        "--event", required=True,
        help='Nombre del evento (ej: "FUR Speech Import Completed")',
    )
    parser.add_argument(
        "--days", type=int, default=None,
        help="Ultimos N dias (default: 7)",
    )
    parser.add_argument(
        "--from", dest="from_date", default=None,
        help="Fecha inicio (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--to", dest="to_date", default=None,
        help="Fecha fin (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--where", default=None,
        help='Filtro Mixpanel (ej: \'properties["form-name"] == "FUR Speech"\')',
    )
    parser.add_argument(
        "--json", dest="output_json", action="store_true",
        help="Output en JSON en vez de tabla",
    )

    args = parser.parse_args()

    from_date, to_date = _resolve_dates(args.from_date, args.to_date, args.days)

    client = MixpanelClient()
    summary = full_event_summary(
        client=client,
        event=args.event,
        from_date=from_date,
        to_date=to_date,
        where=args.where,
    )

    if args.output_json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        _print_table(summary)


if __name__ == "__main__":
    main()
