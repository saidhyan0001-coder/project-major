import argparse

from app.database import init_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize the hotel delivery database")
    parser.add_argument("command", choices=["init-db"], nargs="?", default="init-db")
    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
        print("Database initialized")


if __name__ == "__main__":
    main()
