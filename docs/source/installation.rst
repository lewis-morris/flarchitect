Installation
=========================================

Prerequisites
-------------
Flarchitect supports Python 3.10 or newer. Ensure Python is available and up to date by checking the version:

.. code-block:: bash

  $ python --version

Set up a virtual environment
----------------------------
Using a virtual environment keeps your project's dependencies tidy. Create and activate one:

.. code-block:: bash

  $ python -m venv .venv
  $ source .venv/bin/activate  # On Windows use: .venv\\Scripts\\activate

Install Flarchitect
-------------------
Once the environment is active, install with :program:`pip`:

.. code-block:: bash

  (.venv) $ pip install flarchitect

Verify the installation
-----------------------
Confirm the installation by importing flarchitect and printing its version:

.. code-block:: bash

  (.venv) $ python -c "import flarchitect; print(flarchitect.__version__)"

This quick check ensures Flarchitect is ready to use.
