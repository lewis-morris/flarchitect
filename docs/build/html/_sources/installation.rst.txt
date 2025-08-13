Installation
=========================================

Creating a Virtual Environment
------------------------------
Using a virtual environment keeps dependencies isolated. Create and activate one
with :mod:`venv`::

  $ python -m venv .venv
  $ source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

Minimum Requirements
--------------------
* Python 3.10+
* Flask 2.2.5+
* SQLAlchemy 1.4+ (via :mod:`flask_sqlalchemy` 3.0.5+)

Install FLArchitect
-------------------
Once the environment is active, install with :program:`pip`::

  (.venv) $ pip install flarchitect

Verify the Installation
-----------------------
Run a tiny script to ensure everything works. Create ``verify.py``::

  from flarchitect import Architect
  from flask import Flask

  app = Flask(__name__)
  architect = Architect(app)

  print("FLArchitect is ready!")

Then execute it::

  (.venv) $ python verify.py

Troubleshooting
---------------
* **Missing compiler**: install system build tools (e.g. ``build-essential`` on Ubuntu or Xcode command line tools on macOS).
* **Proxy issues**: set ``HTTP_PROXY``/``HTTPS_PROXY`` environment variables or pass ``--proxy`` to :program:`pip`.

