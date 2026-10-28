"""Dependency-free container health probe; never calls the AI provider."""
import json
from urllib.request import urlopen


def main():
    try:
        with urlopen("http://127.0.0.1:8765/api/v1/health", timeout=3) as response:
            healthy = response.status == 200 and json.load(response).get("status") == "ok"
    except (OSError, ValueError):
        healthy = False
    raise SystemExit(0 if healthy else 1)


if __name__ == "__main__":
    main()
