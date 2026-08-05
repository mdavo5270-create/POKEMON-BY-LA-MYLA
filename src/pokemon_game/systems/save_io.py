from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes


# Save format versioning
SAVE_SCHEMA_VERSION = 1
SAVE_FILE_EXT = ".json"
BACKUP_COUNT = 3


def get_saves_dir() -> Path:
    """Return the recommended saves directory (Windows: %APPDATA%\PokemonByLaMyla\saves).

    Falls back to a local ./saves folder when APPDATA is unavailable.
    """
    appdata = os.getenv("APPDATA")
    if appdata:
        p = Path(appdata) / "PokemonByLaMyla" / "saves"
    else:
        p = Path.cwd() / "saves"
    return p


def slot_path(slot: str) -> Path:
    d = get_saves_dir()
    return d / f"{slot}{SAVE_FILE_EXT}"


def _rotate_backups(path: Path, keep: int = BACKUP_COUNT) -> None:
    """Rotate backups for a given save file: .bak1, .bak2 ... oldest removed."""
    if not path.exists():
        return
    for i in range(keep - 1, 0, -1):
        older = path.with_suffix(path.suffix + f".bak{i}")
        newer = path.with_suffix(path.suffix + f".bak{i+1}")
        if older.exists():
            older.replace(newer)
    # create .bak1 from current file
    first = path.with_suffix(path.suffix + ".bak1")
    try:
        shutil.copy2(path, first)
    except Exception:
        # best-effort backup; ignore failures
        pass


def write_json_atomic(path: Path, data: Dict[str, Any], encrypt: bool = False, password: Optional[str] = None) -> None:
    """Write JSON atomically with temporary file and optional AES-256-GCM encryption.

    - Creates parent dirs.
    - Rotates backups before writing.
    - Uses os.replace for atomic move.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    _rotate_backups(path)

    raw = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

    if encrypt and password:
        raw = _encrypt_bytes(raw, password)

    fd, tmp = tempfile.mkstemp(prefix=path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass


def read_json(path: Path, decrypt: bool = False, password: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Read JSON file, optionally decrypting. Returns None on error."""
    try:
        raw = path.read_bytes()
        if decrypt and password:
            raw = _decrypt_bytes(raw, password)
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


# --- Simple AES helpers (GCM) ---

_SALT_SIZE = 16
_KEY_LEN = 32
_ITER = 100_000
_NONCE_LEN = 12


def _derive_key(password: str, salt: bytes) -> bytes:
    return PBKDF2(password, salt, dkLen=_KEY_LEN, count=_ITER)


def _encrypt_bytes(plain: bytes, password: str) -> bytes:
    salt = get_random_bytes(_SALT_SIZE)
    key = _derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plain)
    # store: salt + nonce + tag + ciphertext
    return salt + cipher.nonce + tag + ciphertext


def _decrypt_bytes(payload: bytes, password: str) -> bytes:
    salt = payload[:_SALT_SIZE]
    nonce = payload[_SALT_SIZE : _SALT_SIZE + _NONCE_LEN]
    tag = payload[_SALT_SIZE + _NONCE_LEN : _SALT_SIZE + _NONCE_LEN + 16]
    ciphertext = payload[_SALT_SIZE + _NONCE_LEN + 16 :]
    key = _derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


# --- Minimal serialization helpers ---


def save_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap data with version metadata for future migrations."""
    return {"schema_version": SAVE_SCHEMA_VERSION, "payload": data}


def load_schema(blob: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(blob, dict):
        return None
    version = blob.get("schema_version")
    if version is None:
        # assume legacy v0 (raw payload)
        return blob
    if version == SAVE_SCHEMA_VERSION:
        return blob.get("payload")
    # future: implement migrations
    raise RuntimeError(f"Unsupported save schema version: {version}")


def to_serializable(obj: Any) -> Any:
    """Try to convert common game objects to JSON-serializable forms.

    Supports dataclasses (asdict), objects with to_dict(), and basic types.
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_serializable(x) for x in obj]
    if is_dataclass(obj):
        return to_serializable(asdict(obj))
    if hasattr(obj, "to_dict"):
        try:
            return to_serializable(obj.to_dict())
        except Exception:
            pass
    # Last resort: try __dict__ (shallow)
    if hasattr(obj, "__dict__"):
        return to_serializable(vars(obj))
    # Fallback to string
    return str(obj)


def build_minimal_save(player: Any, game_map: Any = None) -> Dict[str, Any]:
    """Construct a minimal save payload from game objects.

    The payload contains player position, on_bike, map name, team (list of dicts),
    inventory (if available) and timestamp.
    """
    payload: Dict[str, Any] = {}
    try:
        payload["x"] = float(getattr(player.position, "x", 0))
        payload["y"] = float(getattr(player.position, "y", 0))
    except Exception:
        payload["x"] = 0.0
        payload["y"] = 0.0
    payload["on_bike"] = bool(getattr(player, "on_bike", False))
    # team
    team = getattr(player, "team", None)
    if team and isinstance(team, (list, tuple)):
        payload["team"] = [to_serializable(p) for p in team]
    else:
        payload["team"] = []
    # inventory
    inv = getattr(player, "inventory", None)
    if inv is not None:
        payload["inventory"] = to_serializable(inv)
    # map name
    try:
        payload["map"] = (
            getattr(game_map.current_map, "name")
            if game_map and getattr(game_map, "current_map", None)
            else getattr(game_map, "map_name", None)
        )
    except Exception:
        payload["map"] = None
    return payload


# --- Convenience high-level functions ---


def save_slot(slot: str, player: Any, game_map: Any = None, encrypt: bool = False, password: Optional[str] = None) -> None:
    p = slot_path(slot)
    payload = build_minimal_save(player, game_map)
    wrapped = save_schema(payload)
    write_json_atomic(p, wrapped, encrypt=encrypt, password=password)


def load_slot(slot: str, decrypt: bool = False, password: Optional[str] = None) -> Optional[Dict[str, Any]]:
    p = slot_path(slot)
    blob = read_json(p, decrypt=decrypt, password=password)
    if blob is None:
        return None
    return load_schema(blob)
