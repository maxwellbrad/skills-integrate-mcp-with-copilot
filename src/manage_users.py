"""Provision student and staff accounts without storing plaintext passwords."""

import argparse
from getpass import getpass

from .auth import hash_password, load_users, save_users


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update an activities API account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", choices=("student", "staff"), required=True)
    args = parser.parse_args()

    email = args.email.strip().lower()
    if "@" not in email:
        parser.error("--email must be a valid email address")
    password = getpass("Password: ")
    confirmation = getpass("Confirm password: ")
    if not password or password != confirmation:
        parser.error("Passwords must be non-empty and match")

    users = load_users()
    users[email] = {"role": args.role, "password_hash": hash_password(password)}
    save_users(users)
    print(f"Saved {args.role} account for {email}")


if __name__ == "__main__":
    main()