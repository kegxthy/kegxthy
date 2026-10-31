"""Local administrator maintenance. Backups contain private data; protect/delete them separately."""

import argparse
from task_store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["cleanup", "backup"])
    parser.add_argument("--destination")
    args = parser.parse_args()
    store = Store()
    if args.action == "cleanup":
        # Run while the application is stopped: no active-job lease is shared across processes.
        print({"expired_tasks_deleted": store.cleanup()})
    elif not args.destination:
        parser.error("backup requires --destination")
    else:
        store.backup(args.destination)
        print("SQLite backup created; apply a separate backup retention policy.")


if __name__ == "__main__":
    main()
