"""Tiny client demonstrating how to call the GraphQL demo."""

from __future__ import annotations

import requests


def main() -> None:
    """Run a sample query against the demo server.

    Fetches all items using the ``all_items`` query.
    """
    query: str = """
    query {
        all_items {
            id
            name
        }
    }
    """
    response = requests.post("http://localhost:5000/graphql", json={"query": query})
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()
