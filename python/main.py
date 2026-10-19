import os
from pathlib import Path
from granian import Granian

# Carrega variáveis do arquivo .env se existir
CURRENT_DIR = Path(__file__).resolve().parent
for env_path in (CURRENT_DIR.parent / ".env", CURRENT_DIR / ".env"):
    if env_path.is_file():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip("'").strip('"')
                if key and key not in os.environ:
                    os.environ[key] = val

if __name__ == "__main__":
    app_env = os.getenv("APP_ENV", "development").lower()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    default_reload = "false" if app_env == "production" else "true"
    reload = os.getenv("RELOAD", default_reload).lower() in ("true", "1", "yes")

    server = Granian(
        "app:app",
        address=host,
        port=port,
        workers=workers,
        interface="asgi",
        reload=reload,
    )
    server.serve()
