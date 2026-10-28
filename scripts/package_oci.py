"""Package deployment sources without credentials, runtime databases or dev files."""
import argparse
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "Dockerfile", ".dockerignore", "compose.yaml", "compose.https.yaml",
    ".env.production.example", "deploy/.env.https.example", "deploy/Caddyfile",
    "deploy/healthcheck.py", "requirements-runtime.lock",
    "package.json", "package-lock.json", "dan_gian_config.json", "README.md",
    "docs/oci_docker.md", "docs/dokploy.md", "docs/security_deployment.md", "scripts/smoke_docker.py", "scripts/package_oci.py",
    "research_tools/__init__.py", "research_tools/interpretation_prompt.py",
    "research_tools/date_interpretation_prompt.py", "research_tools/reading_strategy.py",
)
DIRECTORIES = ("randomyst", "config", "schemas", "data/reference", "data/interpretation",
               "data/date_calendar", "docs/prompts", "web")


def include(path):
    relative = path.relative_to(ROOT)
    return (path.is_file() and not path.is_symlink()
            and not any(part.startswith(".") or part in {"__pycache__", "node_modules"} for part in relative.parts)
            and path.suffix.lower() not in {".pyc", ".pyo", ".sqlite3", ".sqlite", ".db", ".pem", ".key"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    paths = {ROOT / name for name in FILES}
    for directory in DIRECTORIES:
        paths.update(path for path in (ROOT / directory).rglob("*") if include(path))
    # Exclusive create prevents accidentally replacing an existing deployment bundle.
    with args.output.open("xb") as stream:
        with tarfile.open(fileobj=stream, mode="w:gz") as archive:
            for path in sorted(paths):
                archive.add(path, arcname=Path("arcana") / path.relative_to(ROOT), recursive=False)
    print(f"Packaged {len(paths)} files: {args.output}")


if __name__ == "__main__":
    main()
