# Release and deployment

Genopedia is an offline-first Python package and command-line tool, not a hosted web service. Its normal deployment path is to build Python distributions and publish them to a package index; users then run it locally.

## Before the first PyPI publication

1. Confirm that the normalized PyPI project name `genopedia` is available or that this project has publication rights to it. If not, change `project.name` in `pyproject.toml` and the release workflow's project URL before publishing.
2. Configure a PyPI Trusted Publisher for this repository. Use GitHub owner `minagayid`, repository `genopedia`, workflow filename `release.yml`, and environment name `pypi`. Start at <https://pypi.org/manage/account/publishing/>.
3. Create the GitHub Actions environment named `pypi` and require an authorized reviewer to approve publication. The workflow grants `id-token: write` only to the publishing job and does not require a long-lived PyPI API token.
4. Protect release tags and restrict who can publish GitHub releases. Publishing occurs only after a GitHub Release is published and the build/test job passes.

## Release checklist

1. Update the literal `__version__` in `genopedia/__init__.py`. The distribution version is derived from this value, so the import package and PyPI metadata cannot silently drift.
2. Run locally:
   ```bash
   python -m unittest discover -s tests -v
   python -m pip install --upgrade build twine
   python -m build --sdist --wheel
   python -m twine check --strict dist/*
   ```
3. Push a tag matching the version, for example `v0.3.0`, and create a GitHub Release for that tag. The release workflow rejects tag/version mismatches.
4. Review the CI and approved publishing job. After PyPI confirms publication, test installation in a fresh virtual environment and run `genopedia demo` and `genopedia reference validate`.

## Scope and safety

Genopedia produces local analysis reports and metadata plans; this release pipeline does not deploy a clinical service or upload research datasets. Keep production datasets, patient information, credentials, and generated sensitive reports out of CI artifacts. The software remains research-use only and does not provide diagnosis, treatment recommendations, or automatic sequence editing.
