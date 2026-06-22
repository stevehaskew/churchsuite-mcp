# Contributing

## Setup

```bash
uv sync
```

## Running tests

```bash
uv run pytest
```

## Adding or changing tools

If your change adds or modifies a tool that calls a new ChurchSuite endpoint,
follow the "Required checks for every change" section in
[CLAUDE.md](CLAUDE.md):

- Verify the endpoint's required OAuth scope against what's configured in
  `TokenManager` (`src/churchsuite_mcp/auth.py`). If it needs a scope not
  already granted, call that out in your PR description — granting a new
  scope happens out-of-band with ChurchSuite, not via code.
- Add or update tests in `tests/test_tools.py`.
- Update the "Known gaps" section of [CLAUDE.md](CLAUDE.md) if the change
  reveals a new API limitation, or resolves a previously documented one.

## Pull requests

Open a PR against `main`. CI runs the test suite across Python 3.10–3.13;
make sure it's green before requesting review.
