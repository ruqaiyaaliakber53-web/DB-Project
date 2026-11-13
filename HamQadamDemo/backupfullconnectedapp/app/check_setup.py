"""
Run this FIRST:   python check_setup.py
It checks Python packages, the SQL Server driver, and the database connection,
and tells you in plain English what to fix.
"""
import sys

print("Python:", sys.version.split()[0])
try:
    from PyQt6.QtCore import PYQT_VERSION_STR
    print("[OK] PyQt6", PYQT_VERSION_STR)
except Exception as e:
    print("[FIX] PyQt6 missing ->  pip install PyQt6      (", e, ")")

try:
    import pyodbc
    print("[OK] pyodbc", pyodbc.version)
except Exception as e:
    print("[FIX] pyodbc missing ->  pip install pyodbc    (", e, ")")
    sys.exit(1)

import config
drivers = pyodbc.drivers()
print("ODBC drivers found:", drivers or "none")
if not any("ODBC Driver" in d for d in drivers):
    print("[FIX] Install 'Microsoft ODBC Driver 18 for SQL Server' (free, from Microsoft), then run this again.")

from db import Database
d = Database()
if d.kind == "sqlserver":
    print("[OK] Connected to", d.description)
    try:
        n = d.query("SELECT COUNT(*) FROM Student")[0][0]
        print(f"[OK] Student table exists ({n} rows).")
    except Exception as e:
        print("[FIX] Connected, but tables are missing -> run sql/01_schema.sql then sql/02_sample_data.sql in SSMS.", e)
else:
    print("[FIX] Could not connect to SQL Server. Reason:", d.fallback_reason)
    print("  1. Is SERVER in config.py exactly what SSMS shows in 'Server name'?  Currently:", config.SERVER)
    print("  2. Is the SQL Server service running?  (Win+R -> services.msc -> 'SQL Server (YOURINSTANCE)' = Running)")
    print("  3. Did you run sql/01_schema.sql in SSMS (it creates the HamQadam database)?")
    print("  4. 'Login failed'  -> set USE_WINDOWS_AUTH = False in config.py and fill USER / PASSWORD.")
