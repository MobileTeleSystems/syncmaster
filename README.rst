.. title

==========
SyncMaster
==========


Requirements
============

Python 3.11+ Poetry 1.5+

.. documentation

Documentation
=============

.. wiki

Wiki page
=========

.. install

Installation
============

.. developing

Develop
=======

Clone repo
----------

.. code:: bash

    git clone git@gitlab.services.mts.ru:bigdata/platform/onetools/syncmaster.git -b develop

    cd syncmaster/

Setup environment
-----------------

Create virtualenv and install dependencies:

.. code:: bash

    cp .env.dev .env
    python -m venv .venv/
    source .venv/bin/activate
    pip install -U pip poetry
    cd syncmaster/
    poetry install --no-root

Run
---



Enable pre-commit hooks
-----------------------

Install pre-commit hooks:

.. code:: bash

    pre-commit install --install-hooks

Test pre-commit hooks run:

.. code:: bash

    pre-commit run

Run pre-commit hooks on whole repo:

.. code:: bash

    pre-commit run --all-files

.. tests

Unit tests
----------

Run unit tests with ``pytest``

.. code:: bash
    cd syncmaster/
    poetry run pytest -v ./tests

.. Makefile

Makefile
--------

Most commands have their own aliases in the makefile for more convenient use.

User ``make help`` for show all available commands.