# Streamlit Demo

This folder is a self-contained Streamlit demo package. It does not depend on files elsewhere in the repo.

## Contents

- `app.py`: Streamlit entrypoint
- `requirements.txt`: app-only dependencies
- `data/competitors/`: bundled competitor JSON files
- `data/news/`: bundled industry and company news JSON files

## Run locally

From the repo root:

```powershell
streamlit run demo\app.py
```

Or from inside the `demo` folder:

```powershell
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

### If you push the whole repo to GitHub

Use:

- Repository: your GitHub repo
- Branch: your target branch
- Main file path: `demo/app.py`

### If you create a separate GitHub repo with only this folder's contents

Upload the contents of `demo/` as the repo root and use:

- Main file path: `app.py`

## Dependencies

Install with:

```powershell
pip install -r demo\requirements.txt
```

Or, if `demo/` is the repo root:

```powershell
pip install -r requirements.txt
```

## Notes

- The app reads only from files inside `demo/data/`.
- No environment variables are required for the demo deployment.
