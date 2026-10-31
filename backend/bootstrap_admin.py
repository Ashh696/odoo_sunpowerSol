#!/usr/bin/env python
"""
Super Admin bootstrap CLI utility.
Can be executed as:
    python bootstrap_admin.py --email admin@sunpower.local --password 'SecureAdminPass123!'
Or reads from environment variables:
    BOOTSTRAP_ADMIN_EMAIL
    BOOTSTRAP_ADMIN_PASSWORD
    BOOTSTRAP_ADMIN_NAME
    BOOTSTRAP_ADMIN_PHONE
"""
import sys
import os
import argparse

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.services.bootstrap import bootstrap_super_admin
from app.services.seed import seed_reference_data


def main():
    parser = argparse.ArgumentParser(description="Bootstrap the initial SunPower SIMS Super Admin.")
    parser.add_argument(
        "--email",
        default=os.getenv("BOOTSTRAP_ADMIN_EMAIL"),
        help="Super admin email address"
    )
    parser.add_argument(
        "--password",
        default=os.getenv("BOOTSTRAP_ADMIN_PASSWORD"),
        help="Super admin password (minimum 8 characters)"
    )
    parser.add_argument(
        "--name",
        default=os.getenv("BOOTSTRAP_ADMIN_NAME", "SunPower Super Admin"),
        help="Full name of super administrator"
    )
    parser.add_argument(
        "--phone",
        default=os.getenv("BOOTSTRAP_ADMIN_PHONE"),
        help="Optional contact phone number"
    )
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Only seed system roles and permissions without creating an admin user"
    )

    args = parser.parse_args()
    db = SessionLocal()

    try:
        if args.seed_only:
            print("[INFO] Seeding system roles and permissions...")
            res = seed_reference_data(db)
            print(f"[SUCCESS] Reference data seeded: {res}")
            return

        email = args.email
        password = args.password

        if not email or not password:
            print("[ERROR] Email and password are required. Provide --email and --password, or set BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD environment variables.")
            sys.exit(1)

        print(f"[INFO] Initializing bootstrap for admin email: {email}")
        user, created = bootstrap_super_admin(
            db=db,
            email=email,
            password=password,
            full_name=args.name,
            phone=args.phone,
        )

        if created:
            print(f"[SUCCESS] Created initial Super Admin account (ID: {user.id}, Email: {user.email})")
        else:
            print(f"[NOTICE] Super Admin account already exists (ID: {user.id}, Email: {user.email}). No changes made.")

    except Exception as e:
        print(f"[ERROR] Bootstrap failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
