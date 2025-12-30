# Copilot / AI Agent Instructions for project370

Purpose: Quickly bring an AI coding agent up to speed so it can make safe, targeted changes.

1) Big-picture architecture
- Django monolithic project: top-level `manage.py` bootstraps the app and `project370/` contains project settings and URLs.
- Main app: `core/` — contains models, views, urls, templates and migrations. Look there first for domain logic.
- Templates: `templates/` organizes UI by area (e.g. `dashboard/`, `registration/`). Use these when changing view rendering.

2) Developer workflows / common commands
- Use Pipenv (there is a `Pipfile`). Typical workflow:
  - `pipenv install` to create environment
  - `pipenv shell` or `pipenv run python manage.py <command>` to run Django commands
- DB / migrations:
  - `pipenv run python manage.py makemigrations` then `pipenv run python manage.py migrate`
- Run server & tests:
  - `pipenv run python manage.py runserver`
  - `pipenv run python manage.py test`

3) Project-specific conventions & patterns
- Single app `core` holds most features — prefer making atomic changes there and updating migrations. See `core/migrations/` for naming patterns (e.g. `0003_rename_rent_amount_property_price_and_more.py`).
- Templates are grouped by area. Use existing template names when adding views (e.g. add dashboard pages under `templates/dashboard/`).
- URL routing: project-level URLs in `project370/urls.py` delegate app routes to `core/urls.py` — update both when introducing new top-level paths.

4) Integration points & external dependencies
- Settings: configuration and installed apps in `project370/settings.py` — check for DB, static/media, and third-party apps before changing imports.
- Static/assets: `Assets/` likely used for frontend assets; confirm before changing template asset links.

5) Safe change checklist for PRs
- Run migrations locally and ensure `pipenv run python manage.py migrate` succeeds.
- Run the test suite: `pipenv run python manage.py test` and fix failing tests caused by changes.
- When changing models, add/inspect migration files in `core/migrations/` — follow existing naming style.

6) Useful files to inspect first (examples)
- `manage.py` — project entry point
- `Pipfile` — dependency manager
- `project370/settings.py` — configuration
- `project370/urls.py` and `core/urls.py` — routing
- `core/views.py`, `core/models.py`, `core/templates/` — domain logic and UI
- `core/migrations/` — migration history (naming shows field renames and structural changes)

7) When to ask the human
- Database credentials or deployment secrets.
- Conflicting migrations or ambiguous data migrations (ask before data-loss changes).

If anything above is unclear or you want more examples (e.g., typical view->template changes or an example migration), tell me which area to expand.
