import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.services.auth import get_user_by_identifier
from app.services.roles import ADMIN_ROLE_CODE, grant_admin_role, user_role_count


def parse_args() -> argparse.Namespace:
    """CLI에서 admin role을 부여할 기존 사용자의 login_id를 읽습니다."""

    parser = argparse.ArgumentParser(description="Grant the admin role to an existing user.")
    parser.add_argument("--login-id", required=True, help="Existing user's login ID")
    return parser.parse_args()


def main() -> None:
    """기존 사용자에게 admin role을 중복 없이 부여합니다."""

    args = parse_args()

    with SessionLocal() as db:
        user = get_user_by_identifier(db, args.login_id)
        if user is None:
            raise SystemExit(f"user not found: {args.login_id}")

        before_count = user_role_count(db, user=user, role_code=ADMIN_ROLE_CODE)
        grant_admin_role(db, user=user)
        after_count = user_role_count(db, user=user, role_code=ADMIN_ROLE_CODE)
        db.commit()

    action = "already had" if before_count == after_count else "granted"
    print(f"{action} admin role: {args.login_id}")


if __name__ == "__main__":
    main()
