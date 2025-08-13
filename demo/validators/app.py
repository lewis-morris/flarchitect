"""Demo application showcasing request validation."""

from __future__ import annotations

from demo.model_extension.model import create_app

# Enable automatic validation to enforce field validators defined on models.
app = create_app({"API_AUTO_VALIDATE": True})
