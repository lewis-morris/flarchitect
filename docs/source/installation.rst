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

Install Flarchitect
-------------------
Once the environment is active, install with :program:`pip`::

  (.venv) $ pip install flarchitect

