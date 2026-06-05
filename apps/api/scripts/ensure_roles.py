import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.roles import ensure_base_roles


def main() -> None:
    with SessionLocal() as db:
        roles = ensure_base_roles(db)
        role_codes = ", ".join(role.role_code for role in roles)
        db.commit()

    print(f"ensured roles: {role_codes}")


if __name__ == "__main__":
    main()
