# Repository Working Agreement

## Branch scope

- Backend integration work belongs on branch `dl`.
- Do not modify, merge, or push `main`, `lfy`, or another branch without explicit user authorization.
- Before a commit or push, verify that the current branch is `dl`.

## Documentation maintenance

- `README.md` is the authoritative repository structure and startup index.
- When directories or important files are added, removed, moved, or renamed, update the structure and responsibility tables in `README.md` in the same change.
- When commands, ports, environment variables, or startup behavior change, update both `README.md` and `STARTUP.md`.
- `docs/API.md` is the authoritative frontend/backend contract. Update it when an endpoint, request, response, error code, or API behavior changes.
- When the integration architecture changes, update `docs/BACKEND_INTEGRATION.md` as well.

## Verification

- Run relevant tests before reporting completion.
- Do not commit `server/data/store.json`, dependency folders, or build output.

