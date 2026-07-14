# KIP Windows SQLite Demo ZIP External PC Acceptance Result

Test date: 2026-07-13

Test target: `kip-sqlite-demo.zip`

Final result: **FAIL**

This test used only ZIP-extracted deployment folders under `C:\KIPDemo` and `C:\KIP 테스트`. Docker, PostgreSQL, external data.go APIs, and KCYCLE APIs were not used.

## Test Environment

- Windows: Windows 10 Home, version 2009, OS HAL 10.0.26100.1
- CPU architecture: x64-based PC, 64-bit OS
- Python launcher/runtime:
  - `python`: 3.11.5
  - `py`: 3.14.3
- PowerShell: 7.6.3
- Internet connectivity: available to `pypi.org:443`
- Initial port status: no listeners on 8000 or 5001

Personal computer name and real user name were not recorded.

## ZIP Hash

- Expected SHA-256: `46683B1DEDFFE7EB48DB3F6763B7A8E9B095EEB4AF61FABC705EB07731FDFBEC`
- Actual SHA-256: `46683B1DEDFFE7EB48DB3F6763B7A8E9B095EEB4AF61FABC705EB07731FDFBEC`
- Result: PASS

## Extraction

Verified both extraction paths:

- `C:\KIPDemo\kip-sqlite-demo`
- `C:\KIP 테스트\kip-sqlite-demo`

Required package entries existed in both paths:

- `backend`
- `frontend`
- `data`
- `scripts`
- `logs`
- `runtime`
- `install_demo.cmd`
- `start_demo.cmd`
- `stop_demo.cmd`
- `README_FIRST.txt`
- `VERSION`

Result: PASS

## Installation

`install_demo.cmd` completed successfully in both paths.

Confirmed:

- Python 3.11 runtime was usable.
- Package-local `.venv` was created.
- Requirements were installed successfully.
- No password or JWT was generated or printed during install.
- System Python environment was not intentionally modified.

Note: in the Korean path, pip console output showed mojibake for the path text, but installation and execution still worked.

Result: PASS

## Administrator Setup

`scripts\setup_admin.ps1` was tested with non-real acceptance credentials. The actual password and token values are not recorded here.

Confirmed:

- Administrator creation succeeded.
- Re-running the same administrator setup returned `created=0` instead of creating a duplicate.
- The database stored a password hash only.
- Plain password was not found in the users table.
- Setup output did not print the password.

Result: PASS

## Initial Execution

`start_demo.cmd` / `start_demo.ps1` started:

- Backend on `http://127.0.0.1:8000`
- Frontend on `http://127.0.0.1:5001`

Confirmed:

- `/health` returned 200 with `{"status":"ok"}`.
- Frontend root returned HTTP 200.
- Frontend API proxy returned `/api/v1/tracks` successfully.
- PID files were created for package-owned backend/frontend processes.
- No password, JWT, or full `DATABASE_URL` was printed by the launcher.

Result: PASS

## General Screens

Browser UI automation could not be completed because the in-app browser failed to attach to a new tab during this test run.

API-level checks for the same local demo data passed:

- Tracks: 3
- Players: 10
- Races: 3
- Race detail included entries
- Track detail returned successfully

Result: FAIL for required browser UI acceptance coverage.

## Administrator Screens

Browser UI automation could not be completed for the same browser attach issue.

API-level administrator checks passed:

- Login returned bearer token.
- External players: 10
- External player statistics: 10
- Match candidates: 10
- Data quality summary: `UNIQUE_CANDIDATE=10`, `total_statistics=10`, `unique_candidate_rate=100.0`
- Unauthenticated admin access returned 401.
- Read-only staging POST returned 405.
- CSV import dry-run for tracks returned `dry_run=true`, `created=0`, `updated=0`, `skipped=3`, `failed=0`.

Result: FAIL for required browser UI acceptance coverage.

## Restart

Verified stop/start behavior:

- After stop, demo ports were released.
- After restart, backend health returned 200.
- Existing administrator login still worked before reset.
- External player data remained at 10 rows.
- No duplicate seed data was observed.

Note: `.cmd` wrappers end with `pause`, so automated shells may appear to hang unless a key/newline is provided. This is acceptable for an interactive Windows user, but inconvenient for unattended acceptance automation.

Result: PASS

## Port Change

After stopping the default demo, the following environment variables were tested:

- `KIP_BACKEND_PORT=8100`
- `KIP_FRONTEND_PORT=5101`

Confirmed:

- Backend health worked on 8100.
- Frontend worked on 5101.
- API proxy worked through 5101.
- Default 8000/5001 listeners were not used during this check.

Result: PASS

## Port Collision

Port 8000 was occupied by a test listener, then `start_demo.ps1 -NoBrowser` was executed.

Confirmed:

- Startup failed with exit code 1.
- Error message identified port 8000 and suggested `KIP_BACKEND_PORT`.
- Existing listener was not stopped.
- No frontend half-process remained on 5001.
- No PID files were left behind.

Result: PASS

## Reset

`scripts\reset_demo.ps1` was tested with the required `RESET` confirmation.

Confirmed:

- Confirmation string was required.
- Existing demo DB was backed up.
- New synthetic DB was created.
- Alembic revision was `0006_external_player_statistics`.
- Counts after reset:
  - users: 0
  - tracks: 3
  - players: 10
  - races: 3
  - external_players: 10
  - external_player_statistics: 10
- Administrator login failed with 401 before re-running admin setup.
- Only the package-local `data\kip_demo.db` was reset.

Result: PASS

## Log Security

Checked:

- `backend.log`
- `backend.error.log`
- `frontend.log`
- `frontend.error.log`
- `launcher.log`

No hits found for:

- password
- Authorization
- Bearer
- JWT secret
- DATABASE_URL
- actual admin email used in the test
- actual service key value

Issue found:

- `frontend.error.log` contained a Python traceback for `ConnectionAbortedError: [WinError 10053]` when a frontend client connection was aborted.
- The traceback did not expose a password, JWT, service key, or database URL.
- It did expose local Python and package file paths.

Result: FAIL because the acceptance criteria required no unexpected stack trace in logs.

## Removal

Confirmed:

- `stop_demo.ps1` released demo ports.
- No listeners remained on 8000, 5001, 8100, or 5101 after shutdown.
- Runtime PID files were removed.
- No KIP Windows service was found.
- The English-path deployment folder was deleted successfully.
- The Korean/space-path deployment folder was deleted successfully.

Result: PASS

## Package Security

Confirmed absent from the package:

- `.git`
- `.env`
- operating `kip.db`
- source maps
- Flutter `.symbols`
- fixed production JWT secret

No actual data.go service key was found. Literal `serviceKey` parameter names exist in unused backend collector code, but no real key value was present.

Result: PASS

## Verification Script

Package verification script result:

- `VERIFY_OK revision=0006_external_player_statistics tracks=3 players=10 races=3 external_players=10 external_player_statistics=10 users=0`

Result: PASS

## Found Problems

1. Required browser UI acceptance coverage could not be completed in this run because the in-app browser failed to attach to a new test tab.
2. `frontend.error.log` can contain a Python traceback for aborted client connections.
3. `.cmd` wrappers include `pause`, which is friendly for manual users but awkward for unattended automation.
4. Korean path installation worked, but pip output displayed mojibake in console text.

## Final Decision

**FAIL**

The ZIP is close to usable: hash, extraction, install, backend/frontend start, admin setup, restart, port change, port collision handling, reset, and removal all passed.

It should not be marked external-PC acceptance PASS yet because required UI screen validation was not completed and a frontend server stack trace appeared in logs.
