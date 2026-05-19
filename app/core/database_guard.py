from pathlib import Path
from urllib.parse import unquote, urlparse

PROTECTED_DB_NAMES = {"tcg_trove.db"}
LOCAL_APP_ENVS = {"development", "dev", "test", "testing", "local"}


def resolve_sqlite_path(database_url: str, *, project_root: Path) -> Path | None:
    normalized_url = database_url.strip()
    lower_url = normalized_url.lower()
    for prefix in ("sqlite+aiosqlite:///", "sqlite:///"):
        if lower_url.startswith(prefix):
            raw_path = unquote(normalized_url[len(prefix) :])
            if raw_path in {"", ":memory:"}:
                return None
            db_path = Path(raw_path)
            if not db_path.is_absolute():
                db_path = project_root / db_path
            return db_path.resolve()
    return None


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_homefinder_database_url(database_url: str, *, project_root: Path, app_env: str) -> Path | None:
    db_path = resolve_sqlite_path(database_url, project_root=project_root)
    if db_path is None:
        return None

    if app_env.strip().lower() in LOCAL_APP_ENVS:
        tcgtrove_root = (project_root.parent / "tcgtrove").resolve()
        if db_path.name.lower() in PROTECTED_DB_NAMES or _is_relative_to(db_path, tcgtrove_root):
            raise ValueError(
                "HomeFinder DATABASE_URL points at protected TCGTrove storage; "
                "use a HomeFinder-owned database such as homefinder.db."
            )

    return db_path


def describe_database_url(database_url: str, *, project_root: Path) -> str:
    db_path = resolve_sqlite_path(database_url, project_root=project_root)
    if db_path is not None:
        return f"sqlite:///{db_path}"

    parsed = urlparse(database_url)
    if not parsed.scheme:
        return "unrecognized database URL"

    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port is not None else ""
    database = parsed.path.lstrip("/") or "unknown-db"
    return f"{parsed.scheme}://{host}{port}/{database}"
