# Chapter 6: Registration Service

This directory contains the final code from the chapter walkthrough, without exercise solutions or additional features.

From this directory, install the dependencies with `uv sync`. The final `database.py` uses the local PostgreSQL connection shown in the chapter. Start that database, run `uv run python check_db.py`, then `uv run alembic upgrade head` and `uv run fastapi dev main.py`.

Run the chapter's eight tests with `uv run pytest -v`. They use SQLite and do not require PostgreSQL.

The Alembic scaffold comes from `alembic init -t async alembic`. Its two generated revisions create the users table and add preferences. `script.py.mako` is Alembic's standard template for generating revisions.
