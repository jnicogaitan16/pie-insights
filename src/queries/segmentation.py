"""
Segmentacion de eventos por propiedad.

Permite desglosar eventos por:
- form-name (tipo de formulario)
- colegio/rbd (institucion)
- rut (usuario)

Uso CLI:
    python -m src.queries.segmentation --event "Page View" --on "form-name" --days 7
    python -m src.queries.segmentation --event "FUR Speech Import Completed" --on "rbd" --days 30
"""

import argparse
import json
import logging
from datetime import date, timedelta

from src.client import MixpanelClient
from src.queries.events import BOT_CITIES

logger = logging.getLogger(__name__)


def segment_by_property(
    client: MixpanelClient,
    event: str,
    from_date: str,
    to_date: str,
    on: str,
    where: str | None = None,
) -> dict:
    """
    Segmenta un evento por una propiedad usando la Segmentation API.

    Args:
        on: Propiedad por la que segmentar (e.g. "form-name", "rbd", "rut")

    Returns:
        {
            "event": "...",
            "segmented_by": "form-name",
            "segments": {"FUR Speech": 42, "FUR Psychoped": 15, ...},
            "total": 57
        }
    """
    # Mixpanel espera el formato properties["prop-name"] para la segmentacion
    on_expr = f'properties["{on}"]'

    result = client.segmentation(
        event=event,
        from_date=from_date,
        to_date=to_date,
        on=on_expr,
        where=where,
    )

    values = result.get("data", {}).get("values", {})

    # La API retorna: {"values": {"segment_value": {"2026-09-01": 5, ...}, ...}}
    segments = {}
    for segment_name, date_values in values.items():
        total = sum(date_values.values())
        if total > 0:
            segments[segment_name] = total

    # Ordenar por conteo descendente
    segments = dict(sorted(segments.items(), key=lambda x: x[1], reverse=True))

    return {
        "event": event,
        "from_date": from_date,
        "to_date": to_date,
        "segmented_by": on,
        "segments": segments,
        "total": sum(segments.values()),
        "unique_segments": len(segments),
    }


def segment_users_by_property(
    client: MixpanelClient,
    event: str,
    from_date: str,
    to_date: str,
    on: str,
    where: str | None = None,
) -> dict:
    """
    Segmenta usuarios unicos por propiedad via raw export.
    Filtra bots automaticamente.

    Returns:
        {
            "event": "...",
            "segmented_by": "rbd",
            "segments": {
                "12345": {"events": 10, "users": 3, "user_ids": [...]},
                ...
            }
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

    segments: dict[str, dict] = {}

    for e in real_events:
        props = e.get("properties", {})
        segment_val = props.get(on)
        if not segment_val:
            continue

        segment_key = str(segment_val)
        if segment_key not in segments:
            segments[segment_key] = {"events": 0, "user_ids": set()}

        segments[segment_key]["events"] += 1

        did = props.get("distinct_id")
        if did:
            segments[segment_key]["user_ids"].add(did)

    # Convertir sets a listas y agregar conteo
    result_segments = {}
    for key, data in segments.items():
        result_segments[key] = {
            "events": data["events"],
            "users": len(data["user_ids"]),
            "user_ids": sorted(data["user_ids"]),
        }

    # Ordenar por eventos descendente
    result_segments = dict(
        sorted(result_segments.items(), key=lambda x: x[1]["events"], reverse=True)
    )

    return {
        "event": event,
        "from_date": from_date,
        "to_date": to_date,
        "segmented_by": on,
        "segments": result_segments,
        "total_events": len(real_events),
        "unique_segments": len(result_segments),
    }


# --- CLI ---

def _print_table(data: dict) -> None:
    """Imprime segmentacion formateada."""
    print("=" * 60)
    print(f"SEGMENTACION — {data['event']}")
    print("=" * 60)
    print(f"  Periodo:      {data['from_date']} → {data['to_date']}")
    print(f"  Segmentado por: {data['segmented_by']}")
    print(f"  Segmentos:    {data['unique_segments']}")

    segments = data.get("segments", {})
    if not segments:
        print("\n  Sin datos para este periodo.")
        print("=" * 60)
        return

    # Detectar si es formato simple (count) o detallado (events/users)
    first_val = next(iter(segments.values()))
    is_detailed = isinstance(first_val, dict)

    print()
    if is_detailed:
        print(f"  {'SEGMENTO':<30} {'EVENTOS':>8} {'USUARIOS':>9}")
        print("  " + "-" * 50)
        for name, info in segments.items():
            label = name[:28] if len(name) > 28 else name
            print(f"  {label:<30} {info['events']:>8} {info['users']:>9}")
    else:
        print(f"  {'SEGMENTO':<40} {'TOTAL':>8}")
        print("  " + "-" * 50)
        for name, count in segments.items():
            label = name[:38] if len(name) > 38 else name
            print(f"  {label:<40} {count:>8}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Segmentar eventos de Mixpanel por propiedad",
        prog="python -m src.queries.segmentation",
    )
    parser.add_argument(
        "--event", required=True,
        help='Nombre del evento',
    )
    parser.add_argument(
        "--on", required=True,
        help='Propiedad para segmentar (ej: "form-name", "rbd", "rut")',
    )
    parser.add_argument(
        "--days", type=int, default=None,
        help="Ultimos N dias",
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
        help="Filtro Mixpanel",
    )
    parser.add_argument(
        "--detailed", action="store_true",
        help="Usar export para conteo de usuarios unicos por segmento",
    )
    parser.add_argument(
        "--json", dest="output_json", action="store_true",
        help="Output en JSON",
    )

    args = parser.parse_args()

    from src.queries.events import _resolve_dates
    from_date, to_date = _resolve_dates(args.from_date, args.to_date, args.days)

    client = MixpanelClient()

    if args.detailed:
        data = segment_users_by_property(
            client=client,
            event=args.event,
            from_date=from_date,
            to_date=to_date,
            on=args.on,
            where=args.where,
        )
    else:
        data = segment_by_property(
            client=client,
            event=args.event,
            from_date=from_date,
            to_date=to_date,
            on=args.on,
            where=args.where,
        )

    if args.output_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        _print_table(data)


if __name__ == "__main__":
    main()
