# ContactDesk UI refresh

This update refreshes the shared navigation, page layout, tables, forms, and CSV import/success screens with a consistent blue-accented responsive design. The Flask routes and database logic are intentionally unchanged.

## Apply safely

1. Back up your existing project and database first.
2. Copy the updated `templates/` and `static/style.css` into your local project, or compare the files in your IDE before replacing them.
3. Keep your existing `app.py`, `database.db`, virtual environment, and any local configuration unchanged for this UI-only pass.
4. Start the app locally and check contacts, contact edit/add, companies, departments, roles, and CSV import before deploying.

The pages continue to use the Bootstrap and DataTables CDN resources already used by the project. An internet connection is needed to load those assets.

## Security note

The current `app.py` contains a hard-coded Flask `SECRET_KEY`. Before a public deployment, move it to an environment variable and use a long random value. Do not upload database files or real personal data to public repositories.
