"""
Healthcheck de conexion a Mixpanel API.

Uso:
    python -m src.healthcheck

Retorna:
    OK — si la conexion es exitosa
    ERROR — si la conexion falla (credenciales, red, etc.)
"""

import sys
import os
import logging

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def check_env_vars() -> list[str]:
    """Verifica que las variables de entorno necesarias esten configuradas."""
    missing = []
    if not os.getenv("MIXPANEL_PROJECT_ID"):
        missing.append("MIXPANEL_PROJECT_ID")

    has_secret = bool(os.getenv("MIXPANEL_API_SECRET"))
    has_sa = bool(
        os.getenv("MIXPANEL_SERVICE_ACCOUNT_USERNAME")
        and os.getenv("MIXPANEL_SERVICE_ACCOUNT_PASSWORD")
    )

    if not has_secret and not has_sa:
        missing.append("MIXPANEL_API_SECRET o (MIXPANEL_SERVICE_ACCOUNT_USERNAME + MIXPANEL_SERVICE_ACCOUNT_PASSWORD)")

    return missing


def run_healthcheck() -> bool:
    """Ejecuta el healthcheck completo."""
    print("=" * 50)
    print("PIE-INSIGHTS — Healthcheck")
    print("=" * 50)

    # 1. Verificar variables de entorno
    print("\n[1/3] Verificando variables de entorno...")
    missing = check_env_vars()
    if missing:
        print(f"  ERROR: Variables faltantes:")
        for var in missing:
            print(f"    - {var}")
        print("\n  Copia .env.example a .env y completa los valores:")
        print("    cp .env.example .env")
        return False
    print("  OK — Variables configuradas")

    # 2. Crear cliente
    print("\n[2/3] Inicializando cliente Mixpanel...")
    try:
        from src.client import MixpanelClient
        client = MixpanelClient()
        print(f"  OK — Cliente creado (auth: {client._auth_method})")
        print(f"  Project ID: {client.project_id}")
    except Exception as e:
        print(f"  ERROR — No se pudo crear el cliente: {e}")
        return False

    # 3. Probar conexion
    print("\n[3/3] Probando conexion a Mixpanel API...")
    if client.ping():
        print("  OK — Conexion exitosa")
    else:
        print("  ERROR — No se pudo conectar a Mixpanel")
        print("  Verifica tus credenciales en .env")
        return False

    print("\n" + "=" * 50)
    print("RESULTADO: OK")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = run_healthcheck()
    sys.exit(0 if success else 1)
