"""Interactively add or update a teacher account."""

import getpass
import hashlib
import json
import secrets

from app import PASSWORD_HASH_ITERATIONS, TEACHERS_FILE


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${salt.hex()}${password_hash.hex()}"


def main() -> None:
    username = input("Teacher username: ").strip()
    if not username:
        raise SystemExit("Username cannot be empty.")

    password = getpass.getpass("Teacher password: ")
    if not password:
        raise SystemExit("Password cannot be empty.")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    try:
        teachers = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        teachers = {}
    except json.JSONDecodeError as error:
        raise SystemExit(f"Cannot read {TEACHERS_FILE}: invalid JSON.") from error

    if not isinstance(teachers, dict):
        raise SystemExit(f"Cannot read {TEACHERS_FILE}: expected a JSON object.")
    teachers[username] = {"password_hash": hash_password(password)}
    TEACHERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEACHERS_FILE.write_text(
        json.dumps(teachers, indent=2) + "\n", encoding="utf-8"
    )
    TEACHERS_FILE.chmod(0o600)
    print(f"Teacher account {username!r} saved to {TEACHERS_FILE}.")


if __name__ == "__main__":
    main()
