KIP SQLite Local Demo - Windows
================================

This package is for a single-PC local demonstration only.
It is not a production server and is not intended for multiple simultaneous users.

System requirements
-------------------
- Windows 10 or 11
- 64-bit Python 3.11 or newer (select "Add Python to PATH" during installation)
- Internet access during the first dependency installation only

First installation
------------------
1. Extract or copy the entire kip-sqlite-demo folder to a writable location.
2. Double-click install_demo.cmd.
3. Open PowerShell in this folder and run:
     powershell -ExecutionPolicy Bypass -File scripts\setup_admin.ps1
   Enter your own administrator email and password. The password is hidden and stored only as a hash.
4. Double-click start_demo.cmd.

Start and stop
--------------
- Start: start_demo.cmd
- Stop: stop_demo.cmd
- Demo URL: http://127.0.0.1:5001
- Backend health: http://127.0.0.1:8000/health

Port changes
------------
Set these in the current PowerShell session before start_demo.ps1:
  $env:KIP_BACKEND_PORT = "8100"
  $env:KIP_FRONTEND_PORT = "5101"
The frontend uses a local same-origin proxy, so both ports can be changed without rebuilding.

Data, backup, and reset
-----------------------
- Demo DB: data\kip_demo.db
- Backups made during reset: data\backups\
- Reset: powershell -ExecutionPolicy Bypass -File scripts\reset_demo.ps1
- Reset requires typing RESET, backs up the current demo DB, and removes administrators.
- Create an administrator again after reset with scripts\setup_admin.ps1.

Logs and troubleshooting
------------------------
- logs\backend.log, backend.error.log, frontend.log, frontend.error.log, launcher.log
- Logs rotate to one .1 file after 5 MB when the demo starts.
- If a port is busy, the launcher does not stop that program. Set alternate ports as shown above.
- If PID files remain after a crash, first run stop_demo.cmd. It refuses to stop an unrelated process.
- Reinstall by deleting only the .venv folder and running install_demo.cmd again.

Complete removal
----------------
Stop the demo, optionally copy data\kip_demo.db or data\backups, then delete this entire folder.
No Windows service, registry entry, Docker container, or external database is installed.

Security and limitations
------------------------
- No data.go service key, production JWT secret, .env file, production DB, or default password is included.
- A random in-memory JWT secret is created at each start; existing login sessions expire after restart.
- The included names and statistics are synthetic test data.
- External collection, AI, prediction, payment, and scheduler features are not part of this demo.
