"""Create (or reset the password of) a RivalSense account from the server.

Usage (from the project root):
    python scripts/create_user.py admin@example.com "Ana Ruiz" --role admin
    python scripts/create_user.py rep@example.com "Rep One"          # member
    python scripts/create_user.py rep@example.com "Rep One" --reset  # new password

The password is read without echo (or from RIVALSENSE_PASSWORD for scripts).
Respects DEMO_MODE / DATABASE_URL like the app.
"""

import argparse
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.auth import MIN_PASSWORD, UserError, create_user, list_users, update_user  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a RivalSense user")
    parser.add_argument("email")
    parser.add_argument("name")
    parser.add_argument("--role", choices=["admin", "member"], default="member")
    parser.add_argument("--reset", action="store_true", help="set a new password for an existing account")
    args = parser.parse_args()

    password = os.getenv("RIVALSENSE_PASSWORD") or getpass.getpass(f"Password (min {MIN_PASSWORD} chars): ")
    try:
        if args.reset:
            user = next((u for u in list_users() if u["email"] == args.email.strip().lower()), None)
            if user is None:
                print(f"No account for {args.email}", file=sys.stderr)
                return 1
            update_user(user["id"], password=password)
            print(f"Password reset for {user['email']} (all their sessions were signed out).")
        else:
            user = create_user(args.email, args.name, password, args.role)
            print(f"Created {user['role']} {user['email']}.")
    except UserError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
