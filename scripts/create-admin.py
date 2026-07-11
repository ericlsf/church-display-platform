#!/usr/bin/env python3
import argparse, getpass, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'hub'))
from services.auth import create_user, init_auth_db, user_count

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('--display-name', default='')
    parser.add_argument('--password', default='')
    args = parser.parse_args()
    password = args.password or getpass.getpass('Password (minimum 10 characters): ')
    confirm = args.password or getpass.getpass('Confirm password: ')
    if password != confirm:
        raise SystemExit('Passwords do not match.')
    init_auth_db(); create_user(args.username, password, 'admin', args.display_name or args.username)
    print(f'Created admin user: {args.username}')
    print(f'Total users: {user_count()}')
if __name__ == '__main__': main()
