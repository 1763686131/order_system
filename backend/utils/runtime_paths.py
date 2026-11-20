"""Resolve bundled resources separately from persistent application data."""

from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONTAINER_ROOT = Path("/app")
_desktop_root = None
_desktop_frontend = None


def configure_desktop(root, frontend):
    """Set desktop paths before importing the Flask app and its routes."""
    global _desktop_root, _desktop_frontend
    _desktop_root = Path(root).resolve()
    _desktop_frontend = Path(frontend).resolve()


def is_desktop():
    return _desktop_root is not None


def frontend_directory():
    if is_desktop():
        return str(_desktop_frontend)
    container_frontend = _CONTAINER_ROOT / "frontend"
    if (container_frontend / "index.html").exists():
        return str(container_frontend)
    return str(_PROJECT_ROOT / "frontend")


def _storage_directory(name, require_frontend):
    if is_desktop():
        return str(_desktop_root / name)
    container_path = _CONTAINER_ROOT / name
    if container_path.is_dir() and (
        not require_frontend or (_CONTAINER_ROOT / "frontend" / "index.html").exists()
    ):
        return str(container_path)
    return str(_PROJECT_ROOT / name)


def data_directory(*, require_frontend=True):
    return _storage_directory("data", require_frontend)


def upload_directory(*, require_frontend=True):
    return _storage_directory("uploads", require_frontend)
