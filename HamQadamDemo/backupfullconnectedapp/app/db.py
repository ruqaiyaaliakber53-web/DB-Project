"""
Database layer. The UI never talks to SQL Server directly; it calls
query() / run() / insert() here. All SQL uses '?' placeholders (parameterised
queries), which also protects against SQL injection.
"""
import os
import re
import sqlite3

import config

try:
    import pyodbc
except ImportError:          # app still works (SQLite fallback) without pyodbc
    pyodbc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SQL_DIR = os.path.join(HERE, "..", "sql")
SQLITE_PATH = os.path.join(HERE, "hamqadam_offline.db")

SQLITE_SCHEMA = """
CREATE TABLE Student (StudentID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT NOT NULL, Email TEXT NOT NULL UNIQUE,
  Password TEXT NOT NULL, Batch INTEGER NOT NULL, Major TEXT NOT NULL, IsEmailVerified INTEGER NOT NULL DEFAULT 0);
CREATE TABLE Admin (AdminID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT NOT NULL, Email TEXT NOT NULL UNIQUE, Password TEXT NOT NULL);
CREATE TABLE Alumnus (AlumniID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT NOT NULL, Email TEXT NOT NULL UNIQUE,
  Password TEXT NOT NULL, GraduationYear INTEGER NOT NULL, Company TEXT NOT NULL, JobTitle TEXT NOT NULL, Industry TEXT, Bio TEXT,
  VerificationStatus TEXT NOT NULL DEFAULT 'Pending' CHECK (VerificationStatus IN ('Pending','Approved','Rejected')),
  VerifiedBy INTEGER REFERENCES Admin(AdminID));
CREATE TABLE Tag (TagID INTEGER PRIMARY KEY AUTOINCREMENT, TagName TEXT NOT NULL,
  Category TEXT NOT NULL CHECK (Category IN ('Industry','Skill')), CreatedBy INTEGER REFERENCES Admin(AdminID), UNIQUE (TagName, Category));
CREATE TABLE StudentInterest (StudentID INTEGER NOT NULL REFERENCES Student(StudentID), TagID INTEGER NOT NULL REFERENCES Tag(TagID),
  PRIMARY KEY (StudentID, TagID));
CREATE TABLE AlumniSkill (AlumniID INTEGER NOT NULL REFERENCES Alumnus(AlumniID), TagID INTEGER NOT NULL REFERENCES Tag(TagID),
  PRIMARY KEY (AlumniID, TagID));
CREATE TABLE Availability (AvailabilityID INTEGER PRIMARY KEY AUTOINCREMENT, AlumniID INTEGER NOT NULL REFERENCES Alumnus(AlumniID),
  SlotDate TEXT NOT NULL, StartTime TEXT NOT NULL, EndTime TEXT NOT NULL, IsBooked INTEGER NOT NULL DEFAULT 0, CHECK (EndTime > StartTime));
CREATE TABLE Session (SessionID INTEGER PRIMARY KEY AUTOINCREMENT, StudentID INTEGER NOT NULL REFERENCES Student(StudentID),
  AlumniID INTEGER NOT NULL REFERENCES Alumnus(AlumniID), AvailabilityID INTEGER NOT NULL REFERENCES Availability(AvailabilityID),
  Status TEXT NOT NULL DEFAULT 'Pending' CHECK (Status IN ('Pending','Confirmed','Rejected','Rescheduled','Completed')),
  Note TEXT, RequestedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE UNIQUE INDEX UX_Session_ActiveSlot ON Session(AvailabilityID) WHERE Status IN ('Pending','Confirmed','Rescheduled','Completed');
CREATE TABLE Feedback (FeedbackID INTEGER PRIMARY KEY AUTOINCREMENT, SessionID INTEGER NOT NULL REFERENCES Session(SessionID),
  GivenBy TEXT NOT NULL CHECK (GivenBy IN ('Student','Alumnus')), Rating INTEGER NOT NULL CHECK (Rating BETWEEN 1 AND 5), Comment TEXT,
  UNIQUE (SessionID, GivenBy));
"""


class DBError(Exception):
    """Friendly database error. kind = 'duplicate' | 'fk' | 'check' | 'other'."""

    def __init__(self, message, kind="other"):
        super().__init__(message)
        self.kind = kind


def _classify(e):
    m = str(e).lower()
    if "unique" in m or "duplicate" in m:
        return DBError("That value already exists (duplicate).", "duplicate")
    if "foreign key" in m:
        return DBError("This record is still referenced by other data.", "fk")
    if "check" in m:
        return DBError("A value broke a database rule (CHECK constraint).", "check")
    return DBError(str(e), "other")


class Database:
    def __init__(self):
        self.kind = None          # 'sqlserver' or 'sqlite'
        self.conn = None
        self.description = ""
        self.fallback_reason = ""
        self._connect()

    # ------------------------------------------------------------------ connect
    def _connect(self):
        if pyodbc is not None and not config.FORCE_SQLITE:
            try:
                self._connect_sqlserver()
                return
            except Exception as e:            # noqa: BLE001
                self.fallback_reason = str(e).splitlines()[0][:200] if str(e) else "unknown error"
        elif pyodbc is None:
            self.fallback_reason = "pyodbc is not installed"
        else:
            self.fallback_reason = "forced offline mode"
        self._connect_sqlite()

    def _connect_sqlserver(self):
        drivers = pyodbc.drivers()
        driver = None
        for wanted in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server",
                       "SQL Server Native Client 11.0", "SQL Server"):
            if wanted in drivers:
                driver = wanted
                break
        if driver is None:
            raise RuntimeError("No SQL Server ODBC driver found")
        parts = [f"DRIVER={{{driver}}}", f"SERVER={config.SERVER}", f"DATABASE={config.DATABASE}"]
        if config.USE_WINDOWS_AUTH:
            parts.append("Trusted_Connection=yes")
        else:
            parts += [f"UID={config.USER}", f"PWD={config.PASSWORD}"]
        if "ODBC Driver" in driver:
            parts.append("TrustServerCertificate=yes")
        self.conn = pyodbc.connect(";".join(parts), autocommit=True, timeout=5)
        self.kind = "sqlserver"
        self.description = f"SQL Server  {config.SERVER}  /  {config.DATABASE}"

    def _connect_sqlite(self):
        fresh = not os.path.exists(SQLITE_PATH)
        self.conn = sqlite3.connect(SQLITE_PATH)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.kind = "sqlite"
        self.description = "OFFLINE practice database (SQLite) - SQL Server not connected"
        if fresh:
            self.conn.executescript(SQLITE_SCHEMA)
            self._load_seed()

    def _load_seed(self):
        path = os.path.join(SQL_DIR, "02_sample_data.sql")
        if not os.path.exists(path):
            return
        text = open(path, encoding="utf-8").read()
        text = re.sub(r"--[^\n]*", "", text)
        for stmt in text.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.upper().startswith("USE "):
                self.conn.execute(stmt)
        self.conn.commit()

    # ------------------------------------------------------------------ helpers
    def query(self, sql, params=()):
        """SELECT -> list of tuples."""
        try:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            rows = [tuple(r) for r in cur.fetchall()]
            cur.close()
            return rows
        except Exception as e:                # noqa: BLE001
            raise _classify(e)

    def run(self, steps):
        """Run several (sql, params) statements as ONE transaction (all or nothing)."""
        try:
            if self.kind == "sqlserver":
                self.conn.autocommit = False
            cur = self.conn.cursor()
            for sql, params in steps:
                cur.execute(sql, params)
            self.conn.commit()
        except Exception as e:                # noqa: BLE001
            try:
                self.conn.rollback()
            except Exception:                 # noqa: BLE001
                pass
            raise _classify(e)
        finally:
            if self.kind == "sqlserver":
                self.conn.autocommit = True

    def execute(self, sql, params=()):
        self.run([(sql, params)])

    def insert(self, sql, params=()):
        """INSERT and return the new identity value."""
        try:
            if self.kind == "sqlserver":
                self.conn.autocommit = False
            cur = self.conn.cursor()
            cur.execute(sql, params)
            if self.kind == "sqlserver":
                cur.execute("SELECT CAST(@@IDENTITY AS INT)")   # @@IDENTITY works with pyodbc parameterised inserts
                new_id = cur.fetchone()[0]
            else:
                new_id = cur.lastrowid
            self.conn.commit()
            return new_id
        except Exception as e:                # noqa: BLE001
            try:
                self.conn.rollback()
            except Exception:                 # noqa: BLE001
                pass
            raise _classify(e)
        finally:
            if self.kind == "sqlserver":
                self.conn.autocommit = True


def fmt_date(v):
    return str(v)[:10]


def fmt_time(v):
    return str(v)[:5]
