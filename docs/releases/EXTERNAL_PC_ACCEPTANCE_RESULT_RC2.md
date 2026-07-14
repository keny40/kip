# KIP Windows SQLite Demo ZIP External PC Acceptance Result RC2

Test date: 2026-07-13

Test target: `kip-sqlite-demo-rc2.zip`

Final result: **PENDING**

RC2 keeps the RC1 scope: ZIP-extracted deployment folders only, no Docker, no PostgreSQL, no external data.go or KCYCLE API calls, and no real password, JWT, or personal email recorded.

## RC2 Package

- Version: `0.1.0-sqlite-demo+rc2-20260713-175613`
- ZIP path: `dist/kip-sqlite-demo-rc2.zip`
- ZIP SHA-256: `1496642B2761E3646991E797D171496D7E6F77A5DC278D2F78C458BA8EE48F60`
- ZIP size: 11,470,636 bytes

## Automatic Checks

- ZIP extraction: PASS
- Install: PASS
- Administrator setup: PASS
- Backend health: PASS
- Frontend static server: PASS
- API proxy: PASS
- Restart: PASS
- Port change: PASS
- Port collision: PASS
- Reset: PASS
- Removal: PASS

## Log Fix Verification

- Client disconnect simulation: PASS
- `ConnectionAbortedError` traceback absent: PASS
- `ConnectionResetError` traceback absent: PASS
- `BrokenPipeError` traceback absent: PASS
- Unexpected server errors still logged: PASS by unit test

Actual local-server disconnect test:

- Repeated partial requests to `/main.dart.js`, then closed the client socket before response completion.
- Subsequent `/` request returned 200.
- Subsequent `/api/v1/tracks` proxy request returned 3 items.
- `frontend.error.log` contained no traceback and no disconnect exception names.

## Chrome/Edge Manual UI Checklist

Status: **PENDING**

Supported manual browsers:

- Latest Chrome
- Latest Edge

Viewport widths to verify:

- 1440
- 1024
- 768
- 390

General screens:

- Today races
- Race detail
- Players
- Player detail
- Tracks
- Track detail
- Analytics

Administrator screens:

- Login
- Admin home
- CSV dry-run
- External players and detail dialog
- External player statistics and detail dialog
- Match candidates
- Data quality
- Logout

KCYCLE external detail links should be checked only where external network access is allowed. If unavailable, classify it as external-network-limited instead of an internal demo failure.

## Security Review

- No actual password: PASS
- No Authorization/Bearer token value: PASS
- No JWT secret: PASS
- No `DATABASE_URL`: PASS
- No actual service key: PASS
- No real administrator email: PASS
- No operating `backend/kip.db`: PASS
- No `.env`: PASS
- No `.git`: PASS
- No source map: PASS
- No debug Flutter build: PASS
- No development PC absolute path in package artifacts: PASS

Note: the literal environment variable name `DATA_GO_KR_SERVICE_KEY` remains in collector code, but no real key value was present and the demo acceptance flow made no external API call.

## Notes

RC2 cannot be marked PASS until Chrome or Edge manual UI verification is completed.
