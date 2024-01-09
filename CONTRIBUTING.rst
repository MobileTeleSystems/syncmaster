Contributing Guide
==================

Welcome! There are many ways to contribute, including submitting bug
reports, improving documentation, submitting feature requests, reviewing
new submissions, or contributing code that can be incorporated into the
project.

Limitations
-----------

We should keep close to these items during development:

* Different users uses SyncMaster in different ways - someone store data in Postgres, someone in MySQL. Such dependencies should be optional.

Initial setup for local development
-----------------------------------

Install Git
~~~~~~~~~~~

Please follow `instruction <https://docs.gitlab.com/ee/topics/git/>`_.

Create a fork
~~~~~~~~~~~~~

If you are not a member of a development team building syncmaster, you should create a fork before making any changes.

Please follow `instruction <https://docs.gitlab.com/ee/user/project/repository/forking_workflow.html>`_.

Clone the repo
~~~~~~~~~~~~~~

Open terminal and run these commands:

.. code:: bash

    git clone https://gitlab.services.mts.ru/myuser/syncmaster.git -b develop

    cd syncmaster

Setup environment
~~~~~~~~~~~~~~~~~

Firstly,Z create virtualenv and install dependencies:

.. code:: bash

    python -m venv .venv/

If you already have venv, but need to install dependencies required for development:

.. code:: bash

    source .venv/bin/activate
    pip install -U pip poetry
    poetry install --no-root

We are using `poetry <https://python-poetry.org/docs/managing-dependencies/>`_ for managing dependencies and building the package.
It allows to keep development environment the same for all developers due to using lock file with fixed dependency versions.

There are dependency **groups*:

* ``backend`` - for running backend
* ``worker`` - for running Celery workers
* ``test`` - for running tests
* ``dev`` - for development, like linters, formatters, mypy, pre-commit and so on

Enable pre-commit hooks
~~~~~~~~~~~~~~~~~~~~~~~

`pre-commit <https://pre-commit.com/>`_ hooks allows to validate & fix repository content before making new commit.
It allows to run linters, formatters, fix file permissions and so on. If something is wrong, changes cannot be committed.

Firstly, install pre-commit hooks:

.. code:: bash

    pre-commit install --install-hooks

Ant then test hooks run:

.. code:: bash

    pre-commit run

How to
------

Run development instance locally
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Firstly, install `make <https://www.gnu.org/software/make/manual/make.html>`_. It is used for running complex commands in local environment.

Start DB and RabbitMQ containers:

.. code:: bash

    docker-compose up -d db rabbitmq

Then start development server:

.. code:: bash

    make run

And open http://localhost:8000/docs

Settings are stored in ``.env.dev`` file.

Working with migrations
~~~~~~~~~~~~~~~~~~~~~~~

Start database:

.. code:: bash

    docker-compose up -d db

Generate revision:

.. code:: bash

    make revision

Upgrade db to ``head`` migration:

.. code:: bash

    make migrate

Run tests locally
~~~~~~~~~~~~~~~~~

Start all containers with dependencies:

.. code:: bash

    docker-compose up -d db rabbitmq test-postgres test-oracle test-hive

Run tests:

.. code:: bash

    make test

Stop all containers and remove created volumes:

.. code:: bash

    docker-compose down -v

Get fixtures not used by any test:

.. code:: bash

    make check-fixtures


Review process
--------------

Please create a new Jira issue for any significant changes and
enhancements that you wish to make. Provide the feature you would like
to see, why you need it, and how it will work. Discuss your ideas
transparently and get community feedback before proceeding.

Significant Changes that you wish to contribute to the project should be
discussed first in a Jira issue that clearly outlines the changes and
benefits of the feature.

Small Changes can directly be crafted and submitted to the Gitlab
Repository as a Merge Request.

Create merge request
~~~~~~~~~~~~~~~~~~~~

Commit your changes:

.. code:: bash

    git commit -m "Commit message"
    git push

Then open Gitlab interface and `create merge request <https://docs.gitlab.com/ee/user/project/merge_requests/>`_.
Please follow guide from MR body template.

After pull request is created, it get a corresponding number, e.g. 123 (``mr_number``).
