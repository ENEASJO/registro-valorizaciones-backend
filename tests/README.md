# Testing guide

This repository separates tests into two categories:

- Unit tests: fast, run in CI on every push/PR
- Integration tests: hit external services (HTTP) or databases (Neon). They are excluded from CI by default and run on-demand.

Conventions
- Integration tests are marked with `@pytest.mark.integration` (or `pytestmark = pytest.mark.integration`).
- Scripts that are primarily manual are guarded by `if __name__ == "__main__":` so importing them in pytest does not execute side effects.

How to run locally
- Unit tests only:
  - `pytest -m "not integration"`
- Integration tests only:
  - Ensure environment variables/secrets are set (e.g., `NEON_CONNECTION_STRING`).
  - `pytest -m integration`

GitHub Actions
- CI workflow (`.github/workflows/ci.yml`) runs unit tests with `-m "not integration"`.
- Integration workflow (`.github/workflows/integration-tests.yml`) can be triggered manually from the GitHub Actions tab and runs only integration tests.
