"""
Settings for connecting the app to SQL Server.
Only SERVER normally needs changing: use EXACTLY what SSMS shows in its
"Server name" box when you connect (e.g.  DESKTOP-AB12CD\\SQLSERVER1  ).
"""
import os

# --- SQL Server connection -------------------------------------------------
SERVER = os.environ.get("HQ_SERVER", r"localhost\SQLEXPRESS")  # "." means this laptop; SQLSERVER1 = your instance name
DATABASE = "HamQadam"

# True  -> Windows login (works if you clicked "Add Current User" during install)
# False -> SQL login using USER / PASSWORD below (the 'sa' password you chose)
USE_WINDOWS_AUTH = True
USER = "sa"
PASSWORD = "your-password-here"

# --- Fallback --------------------------------------------------------------
# If SQL Server cannot be reached, the app runs on a local SQLite copy with the
# same tables + sample data so you can still practise. A banner tells you when
# that happens. Set to True to force it (handy for testing on a PC without SQL Server).
FORCE_SQLITE = os.environ.get("HQ_SQLITE", "0") == "1"
