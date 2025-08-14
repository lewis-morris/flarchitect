"""Application loader for the scaffolding example."""

from __future__ import annotations

from module import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
