import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import or_, select

from app.db.session import SessionLocal
from app.models.auth import User
from app.services.auth import create_user
from app.services.roles import ADMIN_ROLE_CODE, grant_admin_role, user_role_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an admin user or grant admin to an existing one.")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--login-id", required=True, help="Admin login ID")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--display-name", required=True, help="Admin display name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with SessionLocal() as db:
        users = db.scalars(
            select(User).where(or_(User.email == args.email, User.login_id == args.login_id))
        ).all()
        if len({user.user_id for user in users}) > 1:
            raise SystemExit("email and login ID belong to different existing users")

        if users:
            user = users[0]
            created = False
        else:
            user = create_user(
                db,
                email=args.email,
                password=args.password,
                display_name=args.display_name,
                login_id=args.login_id,
                default_allocation_strategy="highest_rate_first",
            )
            created = True

        before_count = user_role_count(db, user=user, role_code=ADMIN_ROLE_CODE)
        grant_admin_role(db, user=user)
        after_count = user_role_count(db, user=user, role_code=ADMIN_ROLE_CODE)
        db.commit()

    if created:
        print(f"created admin user: {args.login_id}")
    elif before_count == after_count:
        print(f"admin user already exists: {args.login_id}")
    else:
        print(f"granted admin role to existing user: {args.login_id}")


if __name__ == "__main__":
    main()
