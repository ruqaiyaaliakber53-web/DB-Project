"""
HamQadam - Alumni Mentorship & Career Network System
PyQt6 desktop app connected to SQL Server.

How the app is organised
  * MainWindow  : the single window. It holds a header (nav buttons) and a
                  QStackedWidget; every screen below is one "page" in that stack.
  * go('name')  : switches to a page  -> this is the screen-to-screen navigation.
  * Page classes: one per screen. Each reads/writes the database through self.db.
Run with:   python main.py
"""
#gfhrjg
import datetime
import sys 

from PyQt6.QtCore import QDate, Qt, QTime
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QInputDialog, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem, QTextEdit, QTimeEdit,
    QVBoxLayout, QWidget,
)

from db import Database, DBError, fmt_date, fmt_time

STYLE = """
* { font-family: 'Segoe UI', 'Noto Sans', Arial; font-size: 13px; color: #0f1b3d; }
QMainWindow, QWidget#page { background: #eef3f8; }
QFrame#card { background: white; border: 1px solid #d5dee8; border-radius: 12px; }
QFrame#header { background: #0f1b3d; }
QFrame#header QLabel { color: white; }
QLabel#brand { font-size: 20px; font-weight: 700; color: white; }
QLabel#h1 { font-size: 22px; font-weight: 700; }
QLabel#h2 { font-size: 15px; font-weight: 600; }
QLabel#muted { color: #6b7a90; }
QLabel#banner { background: #fff3cd; color: #7a5b00; padding: 6px 10px; border-bottom: 1px solid #f0d98a; }
QLabel#stat { font-size: 26px; font-weight: 700; color: #159bb8; }
QLineEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit, QTextEdit {
    background: #f7f9fc; border: 1px solid #cfd8e3; border-radius: 6px; padding: 6px; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #159bb8; }
QPushButton { background: #e4eaf1; border: none; border-radius: 6px; padding: 8px 14px; font-weight: 600; }
QPushButton:hover { background: #d5dee8; }
QPushButton:disabled { background: #eef1f5; color: #a3aebd; }
QPushButton#primary { background: #159bb8; color: white; }
QPushButton#primary:hover { background: #118098; }
QPushButton#danger { background: #e74c3c; color: white; }
QPushButton#danger:hover { background: #c93e2f; }
QPushButton#nav { background: transparent; color: white; padding: 8px 12px; }
QPushButton#nav:hover { background: #1f2f5c; }
QPushButton#navactive { background: #159bb8; color: white; padding: 8px 12px; }
QPushButton#tile { background: white; border: 1px solid #d5dee8; border-radius: 12px; padding: 18px;
    text-align: left; font-size: 14px; }
QPushButton#tile:hover { border: 1px solid #159bb8; background: #f2fbfd; }
QTableWidget, QListWidget { background: white; border: 1px solid #d5dee8; border-radius: 8px;
    alternate-background-color: #f5f8fb; gridline-color: #e6ecf2; }
QHeaderView::section { background: #0f1b3d; color: white; padding: 6px; border: none; font-weight: 600; }
QTableWidget::item:selected, QListWidget::item:selected { background: #cdeef5; color: #0f1b3d; }
"""

# ---- Easy switches (True / False) -------------------------------------------
PLAIN_LOOK = False            # True  = plain default Windows look,  False = the styled teal/navy look
SHOW_DEMO_SHORTCUTS = False  # True  = show the Student/Alumnus/Admin quick-login buttons on the login screen

NAV = {
    "Student": [("My Profile", "s_profile"), ("Find Alumni", "s_search"), ("My Sessions", "sessions")],
    "Alumnus": [("My Profile", "a_profile"), ("My Availability", "a_avail"), ("Session Requests", "sessions")],
    "Admin": [("Verify Alumni", "ad_verify"), ("Manage Tags", "ad_tags"), ("Sessions & Reports", "ad_reports")],
}
TILE_TEXT = {
    "s_profile": "My Profile & Interests\nPick the industries and skills you care about",
    "s_search": "Find Alumni\nSearch and filter verified alumni, then book a session",
    "sessions": "My Sessions\nTrack requests, confirm, complete and leave feedback",
    "a_profile": "My Profile & Expertise\nCompany, industry, bio and skill tags",
    "a_avail": "My Availability\nAdd the time slots students can book",
    "ad_verify": "Verify Alumni\nApprove or reject new alumni accounts",
    "ad_tags": "Manage Tags\nAdd, rename or remove industries and skills",
    "ad_reports": "Sessions & Reports\nAll sessions plus engagement statistics",
}


# ----------------------------------------------------------------------------- helpers
def today():
    return datetime.date.today().isoformat()


def label(text, name=None):
    lb = QLabel(text)
    if name:
        lb.setObjectName(name)
    lb.setWordWrap(True)
    return lb


def button(text, kind=None, slot=None):
    b = QPushButton(text.replace("&", "&&"))   # && so Qt does not treat & as a keyboard shortcut
    if kind:
        b.setObjectName(kind)
    if slot:
        b.clicked.connect(slot)
    return b


def card():
    f = QFrame()
    f.setObjectName("card")
    return f


def make_table(headers):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    t.verticalHeader().setVisible(False)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    t.setAlternatingRowColors(True)
    return t


def fill(table, rows):
    """rows = list of lists; element 0 of each row is the database ID."""
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            table.setItem(r, c, QTableWidgetItem("" if v is None else str(v)))
        table.item(r, 0).setData(Qt.ItemDataRole.UserRole, row[0])


def selected_id(table):
    r = table.currentRow()
    if r < 0 or table.item(r, 0) is None:
        return None
    return table.item(r, 0).data(Qt.ItemDataRole.UserRole)


def guarded(fn):
    """Decorator: show database errors in a message box instead of crashing."""
    def wrapper(self, *args):
        try:
            return fn(self, *args)
        except DBError as e:
            QMessageBox.critical(self, "Database error", str(e))
    return wrapper


def info(parent, msg):
    QMessageBox.information(parent, "HamQadam", msg)


def warn(parent, msg):
    QMessageBox.warning(parent, "HamQadam", msg)


def ask(parent, msg):
    return QMessageBox.question(parent, "HamQadam", msg) == QMessageBox.StandardButton.Yes


def fill_tag_list(lw, tags, selected):
    """Checkable list of tags. tags = [(TagID, TagName, Category)]"""
    lw.clear()
    for tid, name, cat in tags:
        it = QListWidgetItem(name if cat is None else f"{name} - {cat}")
        it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        it.setCheckState(Qt.CheckState.Checked if tid in selected else Qt.CheckState.Unchecked)
        it.setData(Qt.ItemDataRole.UserRole, tid)
        lw.addItem(it)


def checked_tag_ids(lw):
    out = []
    for i in range(lw.count()):
        it = lw.item(i)
        if it.checkState() == Qt.CheckState.Checked:
            out.append(it.data(Qt.ItemDataRole.UserRole))
    return out


class Page(QWidget):
    """Base class for every screen."""

    def __init__(self, win):
        super().__init__()
        self.setObjectName("page")
        self.win = win
        self.db = win.db

    def on_show(self):
        pass

    def layout_with_title(self, title, subtitle=None):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.addWidget(label(title, "h1"))
        if subtitle:
            lay.addWidget(label(subtitle, "muted"))
        return lay


# ============================================================================= SCREEN 1: login + registration
class LoginPage(Page):
    def __init__(self, win):
        super().__init__(win)
        outer = QVBoxLayout(self)
        outer.addStretch()
        box = card()
        box.setFixedWidth(440)
        form = QVBoxLayout(box)
        form.setContentsMargins(28, 24, 28, 24)
        form.setSpacing(8)
        form.addWidget(label("Welcome to HamQadam", "h1"))
        form.addWidget(label("Alumni Mentorship & Career Network System", "muted"))
        form.addSpacing(8)
        self.role = QComboBox()
        self.role.addItems(["Student", "Alumnus", "Admin"])
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.pw = QLineEdit()
        self.pw.setPlaceholderText("Password")
        self.pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw.returnPressed.connect(self.do_login)
        form.addWidget(label("I am a"))
        form.addWidget(self.role)
        form.addWidget(self.email)
        form.addWidget(self.pw)
        form.addWidget(button("Login", "primary", self.do_login))
        form.addWidget(button("Create a new account", None, lambda: win.go("register")))
        if SHOW_DEMO_SHORTCUTS:
            form.addSpacing(6)
            form.addWidget(label("Demo shortcuts (fills in a sample account):", "muted"))
            row = QHBoxLayout()
            row.addWidget(button("Student", None, lambda: self.quick("Student", "sara.ahmed@st.habib.edu.pk")))
            row.addWidget(button("Alumnus", None, lambda: self.quick("Alumnus", "zara.qureshi@alumni.habib.edu.pk")))
            row.addWidget(button("Admin", None, lambda: self.quick("Admin", "admin@habib.edu.pk")))
            form.addLayout(row)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(box)
        h.addStretch()
        outer.addLayout(h)
        outer.addStretch()

    def quick(self, role, email):
        self.role.setCurrentText(role)
        self.email.setText(email)
        self.pw.setText("pass123")
        self.do_login()

    @guarded
    def do_login(self, *_):
        role, email, pw = self.role.currentText(), self.email.text().strip(), self.pw.text()
        if not email or not pw:
            warn(self, "Please enter your email and password.")
            return
        if role == "Student":
            rows = self.db.query("SELECT StudentID, Name, Password, IsEmailVerified FROM Student WHERE Email = ?", (email,))
        elif role == "Alumnus":
            rows = self.db.query("SELECT AlumniID, Name, Password, VerificationStatus FROM Alumnus WHERE Email = ?", (email,))
        else:
            rows = self.db.query("SELECT AdminID, Name, Password, 1 FROM Admin WHERE Email = ?", (email,))
        if not rows or rows[0][2] != pw:
            warn(self, "Incorrect email or password for this role.")
            return
        uid, name, _, flag = rows[0]
        if role == "Student" and not flag:
            warn(self, "Please verify your email first (use the link we sent you).")
            return
        if role == "Alumnus" and flag == "Rejected":
            warn(self, "Your alumni account was rejected by the admin, so you cannot log in.")
            return
        if role == "Alumnus" and flag == "Pending":
            info(self, "Your account is waiting for admin approval.\nYou can set up your profile, but students cannot see you until you are approved.")
        self.email.clear()
        self.pw.clear()
        self.win.login_user(role, uid, name)


class RegisterPage(Page):
    def __init__(self, win):
        super().__init__(win)
        outer = QVBoxLayout(self)
        outer.addStretch()
        box = card()
        box.setFixedWidth(500)
        v = QVBoxLayout(box)
        v.setContentsMargins(28, 24, 28, 24)
        v.addWidget(label("Create an account", "h1"))
        self.role = QComboBox()
        self.role.addItems(["Student", "Alumnus", "Admin"])
        self.name = QLineEdit()
        self.email = QLineEdit()
        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.EchoMode.Password)
        form = QFormLayout()
        form.addRow("Register as", self.role)
        form.addRow("Full name", self.name)
        form.addRow("Email", self.email)
        form.addRow("Password", self.pw)
        v.addLayout(form)
        # role-specific fields
        self.extra = QStackedWidget()
        s = QWidget(); sf = QFormLayout(s)
        self.batch = QSpinBox(); self.batch.setRange(2020, 2035); self.batch.setValue(2028)
        self.major = QLineEdit()
        sf.addRow("Batch", self.batch); sf.addRow("Major", self.major)
        a = QWidget(); af = QFormLayout(a)
        self.grad = QSpinBox(); self.grad.setRange(2000, 2035); self.grad.setValue(2022)
        self.company = QLineEdit(); self.job = QLineEdit()
        af.addRow("Graduation year", self.grad); af.addRow("Current company", self.company); af.addRow("Job title", self.job)
        d = QWidget(); df = QFormLayout(d)
        self.code = QLineEdit(); self.code.setPlaceholderText("Staff code (demo: HU-STAFF)")
        df.addRow("Staff code", self.code)
        for w in (s, a, d):
            self.extra.addWidget(w)
        self.role.currentIndexChanged.connect(self.extra.setCurrentIndex)
        v.addWidget(self.extra)
        v.addWidget(button("Register", "primary", self.submit))
        v.addWidget(button("Back to login", None, lambda: win.go("login")))
        h = QHBoxLayout(); h.addStretch(); h.addWidget(box); h.addStretch()
        outer.addLayout(h); outer.addStretch()

    @guarded
    def submit(self, *_):
        role = self.role.currentText()
        name, email, pw = self.name.text().strip(), self.email.text().strip(), self.pw.text()
        if not name or "@" not in email or len(pw) < 4:
            warn(self, "Enter a name, a valid email and a password (4+ characters).")
            return
        try:
            if role == "Student":
                if not self.major.text().strip():
                    warn(self, "Please enter your major.")
                    return
                self.db.insert("INSERT INTO Student (Name, Email, Password, Batch, Major, IsEmailVerified) VALUES (?,?,?,?,?,1)",
                               (name, email, pw, self.batch.value(), self.major.text().strip()))
                msg = "Student account created.\n(In the final version a verification link is emailed; it is simulated for now.)"
            elif role == "Alumnus":
                if not self.company.text().strip() or not self.job.text().strip():
                    warn(self, "Please enter your company and job title.")
                    return
                self.db.insert("INSERT INTO Alumnus (Name, Email, Password, GraduationYear, Company, JobTitle, VerificationStatus) VALUES (?,?,?,?,?,?,'Pending')",
                               (name, email, pw, self.grad.value(), self.company.text().strip(), self.job.text().strip()))
                msg = "Alumni account created with status 'Pending'.\nAn admin must approve it before students can find you."
            else:
                if self.code.text().strip() != "HU-STAFF":
                    warn(self, "Invalid staff code. Admin accounts need internal verification.")
                    return
                self.db.insert("INSERT INTO Admin (Name, Email, Password) VALUES (?,?,?)", (name, email, pw))
                msg = "Admin account created."
        except DBError as e:
            if e.kind == "duplicate":
                warn(self, "This email is already registered for that role.")
                return
            raise
        info(self, msg)
        for w in (self.name, self.email, self.pw, self.major, self.company, self.job, self.code):
            w.clear()
        self.win.go("login")


# ============================================================================= Home dashboards
class HomePage(Page):
    def __init__(self, win):
        super().__init__(win)
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(28, 20, 28, 20)

    def clear(self):
        while self.lay.count():
            item = self.lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                while item.layout().count():
                    x = item.layout().takeAt(0)
                    if x.widget():
                        x.widget().deleteLater()

    @guarded
    def on_show(self):
        self.clear()
        u = self.win.user
        if not u:
            return
        role, uid = u["role"], u["id"]
        self.lay.addWidget(label(f"Hello, {u['name']}", "h1"))
        self.lay.addWidget(label(f"Signed in as {role}", "muted"))
        stats = []
        if role in ("Student", "Alumnus"):
            col = "StudentID" if role == "Student" else "AlumniID"
            counts = dict(self.db.query(f"SELECT Status, COUNT(*) FROM Session WHERE {col} = ? GROUP BY Status", (uid,)))
            stats = [(k, counts.get(k, 0)) for k in ("Pending", "Confirmed", "Rescheduled", "Completed")]
            if role == "Alumnus":
                st = self.db.query("SELECT VerificationStatus FROM Alumnus WHERE AlumniID = ?", (uid,))[0][0]
                stats.insert(0, ("Account status", st))
        else:
            pend = self.db.query("SELECT COUNT(*) FROM Alumnus WHERE VerificationStatus = 'Pending'")[0][0]
            tot = self.db.query("SELECT COUNT(*) FROM Session")[0][0]
            tags = self.db.query("SELECT COUNT(*) FROM Tag")[0][0]
            stats = [("Alumni awaiting approval", pend), ("Total sessions", tot), ("Tags in taxonomy", tags)]
        row = QHBoxLayout()
        for name, val in stats:
            c = card()
            cl = QVBoxLayout(c)
            cl.addWidget(label(str(val), "stat"))
            cl.addWidget(label(name, "muted"))
            row.addWidget(c)
        self.lay.addLayout(row)
        self.lay.addSpacing(10)
        self.lay.addWidget(label("Where would you like to go?", "h2"))
        grid = QGridLayout()
        for i, (_, key) in enumerate(NAV[role]):
            b = button(TILE_TEXT[key], "tile", lambda _=False, k=key: self.win.go(k))
            b.setMinimumHeight(90)
            grid.addWidget(b, i // 2, i % 2)
        self.lay.addLayout(grid)
        self.lay.addStretch()


# ============================================================================= Student screens
class StudentProfilePage(Page):
    def __init__(self, win):
        super().__init__(win)
        lay = self.layout_with_title("My Profile & Interests", "Choose the industries and skills you want mentorship in. Alumni with matching tags are easier to find.")
        c = card()
        cl = QVBoxLayout(c)
        form = QFormLayout()
        self.name = QLabel()
        self.batch = QSpinBox(); self.batch.setRange(2020, 2035)
        self.major = QLineEdit()
        form.addRow("Name", self.name); form.addRow("Batch", self.batch); form.addRow("Major", self.major)
        cl.addLayout(form)
        cl.addWidget(label("Interests (tick any):", "h2"))
        self.tags = QListWidget()
        cl.addWidget(self.tags)
        cl.addWidget(button("Save profile", "primary", self.save))
        lay.addWidget(c)

    @guarded
    def on_show(self):
        sid = self.win.user["id"]
        name, batch, major = self.db.query("SELECT Name, Batch, Major FROM Student WHERE StudentID = ?", (sid,))[0]
        self.name.setText(name); self.batch.setValue(int(batch)); self.major.setText(major)
        tags = self.db.query("SELECT TagID, TagName, Category FROM Tag ORDER BY Category, TagName")
        sel = {r[0] for r in self.db.query("SELECT TagID FROM StudentInterest WHERE StudentID = ?", (sid,))}
        fill_tag_list(self.tags, tags, sel)

    @guarded
    def save(self, *_):
        sid = self.win.user["id"]
        steps = [("UPDATE Student SET Batch = ?, Major = ? WHERE StudentID = ?", (self.batch.value(), self.major.text().strip(), sid)),
                 ("DELETE FROM StudentInterest WHERE StudentID = ?", (sid,))]
        steps += [("INSERT INTO StudentInterest (StudentID, TagID) VALUES (?, ?)", (sid, t)) for t in checked_tag_ids(self.tags)]
        self.db.run(steps)
        info(self, "Profile saved.")


class SearchPage(Page):
    """SCREEN 4: Alumni search & discovery"""

    def __init__(self, win):
        super().__init__(win)
        lay = self.layout_with_title("Find Alumni", "Only admin-approved alumni appear here. Filters can be combined.")
        row = QHBoxLayout()
        self.name = QLineEdit(); self.name.setPlaceholderText("Search by name...")
        self.name.returnPressed.connect(self.search)
        self.industry = QComboBox(); self.company = QComboBox(); self.skill = QComboBox()
        row.addWidget(self.name, 2)
        for cb in (self.industry, self.company, self.skill):
            row.addWidget(cb, 1)
        row.addWidget(button("Search", "primary", self.search))
        row.addWidget(button("Reset", None, self.reset))
        lay.addLayout(row)
        self.table = make_table(["ID", "Name", "Job title", "Company", "Industry", "Skills"])
        self.table.doubleClicked.connect(self.view)
        lay.addWidget(self.table)
        lay.addWidget(button("View profile & book a session  >", "primary", self.view))

    def _combo(self, cb, first, values):
        cur = cb.currentText()
        cb.clear()
        cb.addItem(first)
        cb.addItems(values)
        i = cb.findText(cur)
        cb.setCurrentIndex(i if i >= 0 else 0)

    @guarded
    def on_show(self):
        self._combo(self.industry, "All industries", [r[0] for r in self.db.query("SELECT TagName FROM Tag WHERE Category = 'Industry' ORDER BY TagName")])
        self._combo(self.skill, "All skills", [r[0] for r in self.db.query("SELECT TagName FROM Tag WHERE Category = 'Skill' ORDER BY TagName")])
        self._combo(self.company, "All companies", [r[0] for r in self.db.query("SELECT DISTINCT Company FROM Alumnus WHERE VerificationStatus = 'Approved' ORDER BY Company")])
        self.search()

    def reset(self, *_):
        self.name.clear()
        for cb in (self.industry, self.company, self.skill):
            cb.setCurrentIndex(0)
        self.search()

    @guarded
    def search(self, *_):
        sql = "SELECT a.AlumniID, a.Name, a.JobTitle, a.Company, a.Industry FROM Alumnus a WHERE a.VerificationStatus = 'Approved' AND a.Name LIKE ?"
        params = ["%" + self.name.text().strip() + "%"]
        if self.industry.currentIndex() > 0:
            sql += " AND a.Industry = ?"; params.append(self.industry.currentText())
        if self.company.currentIndex() > 0:
            sql += " AND a.Company = ?"; params.append(self.company.currentText())
        if self.skill.currentIndex() > 0:
            sql += (" AND EXISTS (SELECT 1 FROM AlumniSkill s JOIN Tag t ON t.TagID = s.TagID"
                    " WHERE s.AlumniID = a.AlumniID AND t.TagName = ? AND t.Category = 'Skill')")
            params.append(self.skill.currentText())
        rows = self.db.query(sql + " ORDER BY a.Name", tuple(params))
        skills = {}
        for aid, tname in self.db.query("SELECT s.AlumniID, t.TagName FROM AlumniSkill s JOIN Tag t ON t.TagID = s.TagID WHERE t.Category = 'Skill' ORDER BY t.TagName"):
            skills.setdefault(aid, []).append(tname)
        fill(self.table, [list(r) + [", ".join(skills.get(r[0], []))] for r in rows])

    def view(self, *_):
        aid = selected_id(self.table)
        if aid is None:
            warn(self, "Select an alumnus first.")
            return
        self.win.pages["s_book"].alumni_id = aid
        self.win.go("s_book")


class BookingPage(Page):
    """SCREEN 5: Mentorship session booking (transaction screen)"""

    def __init__(self, win):
        super().__init__(win)
        self.alumni_id = None
        lay = self.layout_with_title("Book a Mentorship Session")
        body = QHBoxLayout()
        left = card(); ll = QVBoxLayout(left)
        self.who = label("", "h2"); self.headline = label(""); self.industry = label("", "muted")
        self.skills = label(""); self.bio = label("", "muted")
        for w in (self.who, self.headline, self.industry, self.skills, self.bio):
            ll.addWidget(w)
        ll.addStretch()
        right = card(); rl = QVBoxLayout(right)
        rl.addWidget(label("1. Pick an available slot", "h2"))
        self.slots = make_table(["ID", "Date", "Start", "End"])
        rl.addWidget(self.slots)
        rl.addWidget(label("2. What would you like to discuss? (optional)", "h2"))
        self.note = QTextEdit(); self.note.setMaximumHeight(90)
        self.counter = label("0 / 500", "muted")
        self.note.textChanged.connect(lambda: self.counter.setText(f"{len(self.note.toPlainText())} / 500"))
        rl.addWidget(self.note); rl.addWidget(self.counter)
        rl.addWidget(button("Submit session request", "primary", self.request))
        body.addWidget(left, 1); body.addWidget(right, 2)
        lay.addLayout(body)
        lay.addWidget(button("<  Back to search", None, lambda: win.go("s_search")))

    @guarded
    def on_show(self):
        self.note.clear()
        a = self.db.query("SELECT Name, JobTitle, Company, Industry, Bio FROM Alumnus WHERE AlumniID = ?", (self.alumni_id,))[0]
        self.who.setText(a[0]); self.headline.setText(f"{a[1]} at {a[2]}"); self.industry.setText(f"Industry: {a[3] or '-'}")
        sk = [r[0] for r in self.db.query("SELECT t.TagName FROM AlumniSkill s JOIN Tag t ON t.TagID = s.TagID WHERE s.AlumniID = ? AND t.Category = 'Skill' ORDER BY t.TagName", (self.alumni_id,))]
        self.skills.setText("Skills: " + (", ".join(sk) or "-")); self.bio.setText(a[4] or "")
        rows = self.db.query("SELECT AvailabilityID, SlotDate, StartTime, EndTime FROM Availability WHERE AlumniID = ? AND IsBooked = 0 AND SlotDate >= ? ORDER BY SlotDate, StartTime",
                             (self.alumni_id, today()))
        fill(self.slots, [[r[0], fmt_date(r[1]), fmt_time(r[2]), fmt_time(r[3])] for r in rows])

    @guarded
    def request(self, *_):
        slot = selected_id(self.slots)
        if slot is None:
            warn(self, "Please select a time slot.")
            return
        note = self.note.toPlainText().strip()
        if len(note) > 500:
            warn(self, "The note can be at most 500 characters.")
            return
        if self.db.query("SELECT IsBooked FROM Availability WHERE AvailabilityID = ?", (slot,))[0][0]:
            warn(self, "Sorry, that slot was just booked by someone else.")
            self.on_show()
            return
        sid = self.win.user["id"]
        # ONE transaction: create the Session AND mark the slot as booked (all-or-nothing)
        self.db.run([
            ("INSERT INTO Session (StudentID, AlumniID, AvailabilityID, Status, Note, RequestedAt) VALUES (?,?,?,'Pending',?,?)",
             (sid, self.alumni_id, slot, note, datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))),
            ("UPDATE Availability SET IsBooked = 1 WHERE AvailabilityID = ?", (slot,)),
        ])
        info(self, "Request sent! Status: Pending.\nThe alumnus will accept, reject or propose a new time.")
        self.win.go("sessions")


# ============================================================================= Alumnus screens
class AlumniProfilePage(Page):
    """SCREEN 2: Profile & expertise setup (setup screen 1)"""

    def __init__(self, win):
        super().__init__(win)
        lay = self.layout_with_title("My Profile & Expertise", "This is what students see once an admin has approved your account.")
        c = card(); cl = QVBoxLayout(c)
        form = QFormLayout()
        self.company = QLineEdit(); self.job = QLineEdit(); self.industry = QComboBox()
        self.bio = QTextEdit(); self.bio.setMaximumHeight(80)
        self.counter = label("0 / 300", "muted")
        self.bio.textChanged.connect(lambda: self.counter.setText(f"{len(self.bio.toPlainText())} / 300"))
        form.addRow("Company", self.company); form.addRow("Job title", self.job)
        form.addRow("Industry", self.industry); form.addRow("Short bio", self.bio); form.addRow("", self.counter)
        cl.addLayout(form)
        cl.addWidget(label("Skills (tick any):", "h2"))
        self.skills = QListWidget(); cl.addWidget(self.skills)
        cl.addWidget(button("Save profile", "primary", self.save))
        lay.addWidget(c)

    @guarded
    def on_show(self):
        aid = self.win.user["id"]
        co, job, ind, bio = self.db.query("SELECT Company, JobTitle, Industry, Bio FROM Alumnus WHERE AlumniID = ?", (aid,))[0]
        self.company.setText(co); self.job.setText(job); self.bio.setPlainText(bio or "")
        self.industry.clear()
        self.industry.addItems([r[0] for r in self.db.query("SELECT TagName FROM Tag WHERE Category = 'Industry' ORDER BY TagName")])
        i = self.industry.findText(ind or "")
        self.industry.setCurrentIndex(i if i >= 0 else 0)
        tags = [(r[0], r[1], None) for r in self.db.query("SELECT TagID, TagName FROM Tag WHERE Category = 'Skill' ORDER BY TagName")]
        sel = {r[0] for r in self.db.query("SELECT TagID FROM AlumniSkill WHERE AlumniID = ?", (aid,))}
        fill_tag_list(self.skills, tags, sel)

    @guarded
    def save(self, *_):
        aid = self.win.user["id"]
        bio = self.bio.toPlainText().strip()
        if len(bio) > 300:
            warn(self, "The bio can be at most 300 characters.")
            return
        if not self.company.text().strip() or not self.job.text().strip():
            warn(self, "Company and job title are required.")
            return
        steps = [("UPDATE Alumnus SET Company = ?, JobTitle = ?, Industry = ?, Bio = ? WHERE AlumniID = ?",
                  (self.company.text().strip(), self.job.text().strip(), self.industry.currentText(), bio, aid)),
                 ("DELETE FROM AlumniSkill WHERE AlumniID = ?", (aid,))]
        steps += [("INSERT INTO AlumniSkill (AlumniID, TagID) VALUES (?, ?)", (aid, t)) for t in checked_tag_ids(self.skills)]
        self.db.run(steps)
        info(self, "Profile saved. (Verification status is not reset by edits.)")


class AvailabilityPage(Page):
    """SCREEN 3: Availability configuration (setup screen 2)"""

    def __init__(self, win):
        super().__init__(win)
        lay = self.layout_with_title("My Availability", "Add the time slots students can book. A slot that is already linked to a request cannot be deleted.")
        row = QHBoxLayout()
        self.date = QDateEdit(QDate.currentDate().addDays(1)); self.date.setCalendarPopup(True)
        self.start = QTimeEdit(QTime(10, 0)); self.end = QTimeEdit(QTime(10, 30))
        self.weeks = QSpinBox(); self.weeks.setRange(1, 8); self.weeks.setSuffix(" week(s)")
        for t, w in (("Date", self.date), ("Start", self.start), ("End", self.end), ("Repeat weekly for", self.weeks)):
            row.addWidget(label(t, "muted")); row.addWidget(w)
        row.addWidget(button("Add slot", "primary", self.add))
        lay.addLayout(row)
        self.table = make_table(["ID", "Date", "Start", "End", "Status"])
        lay.addWidget(self.table)
        lay.addWidget(button("Delete selected slot", "danger", self.delete))

    @guarded
    def on_show(self):
        rows = self.db.query("SELECT AvailabilityID, SlotDate, StartTime, EndTime, IsBooked FROM Availability WHERE AlumniID = ? ORDER BY SlotDate, StartTime", (self.win.user["id"],))
        fill(self.table, [[r[0], fmt_date(r[1]), fmt_time(r[2]), fmt_time(r[3]), "Booked" if r[4] else "Free"] for r in rows])

    @guarded
    def add(self, *_):
        aid = self.win.user["id"]
        s, e = self.start.time().toString("HH:mm"), self.end.time().toString("HH:mm")
        if e <= s:
            warn(self, "End time must be after the start time.")
            return
        if self.date.date() < QDate.currentDate():
            warn(self, "The date cannot be in the past.")
            return
        steps = []
        for w in range(self.weeks.value()):
            d = self.date.date().addDays(7 * w).toString("yyyy-MM-dd")
            clash = self.db.query("SELECT COUNT(*) FROM Availability WHERE AlumniID = ? AND SlotDate = ? AND StartTime < ? AND EndTime > ?", (aid, d, e, s))[0][0]
            if clash:
                warn(self, f"A slot on {d} overlaps with one you already have.")
                return
            steps.append(("INSERT INTO Availability (AlumniID, SlotDate, StartTime, EndTime, IsBooked) VALUES (?,?,?,?,0)", (aid, d, s, e)))
        self.db.run(steps)
        self.on_show()

    def delete(self, *_):
        slot = selected_id(self.table)
        if slot is None:
            warn(self, "Select a slot first.")
            return
        try:
            if self.db.query("SELECT IsBooked FROM Availability WHERE AvailabilityID = ?", (slot,))[0][0]:
                warn(self, "This slot is linked to an active session and cannot be deleted.")
                return
            self.db.execute("DELETE FROM Availability WHERE AvailabilityID = ?", (slot,))
        except DBError as e:
            warn(self, "This slot has session history (e.g. a rejected request), so it cannot be deleted." if e.kind == "fk" else str(e))
            return
        self.on_show()


# ============================================================================= SCREEN 6: sessions (both roles)
class FeedbackDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Leave feedback")
        v = QVBoxLayout(self)
        self.rating = QComboBox(); self.rating.addItems(["5", "4", "3", "2", "1"])
        self.comment = QTextEdit(); self.comment.setMaximumHeight(90)
        f = QFormLayout(); f.addRow("Rating (1-5)", self.rating); f.addRow("Comment", self.comment)
        v.addLayout(f)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        v.addWidget(bb)


class RescheduleDialog(QDialog):
    def __init__(self, parent, slots):
        super().__init__(parent)
        self.setWindowTitle("Propose a new time")
        v = QVBoxLayout(self)
        v.addWidget(QLabel("Pick one of your free slots to offer the student:"))
        self.combo = QComboBox()
        for sid, d, s, e in slots:
            self.combo.addItem(f"{d}   {s} - {e}", sid)
        v.addWidget(self.combo)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        v.addWidget(bb)


class SessionsPage(Page):
    """Transaction lifecycle: Pending -> Confirmed -> Completed (or Rejected / Rescheduled)"""

    def __init__(self, win):
        super().__init__(win)
        self.info = {}
        lay = self.layout_with_title("Sessions", None)
        self.sub = label("", "muted"); lay.addWidget(self.sub)
        self.table = make_table(["ID", "With", "Date", "Time", "Status", "Note"])
        self.table.itemSelectionChanged.connect(self.update_buttons)
        lay.addWidget(self.table)
        self.fb = label("", "muted"); lay.addWidget(self.fb)
        row = QHBoxLayout()
        self.b_accept = button("Accept", "primary", self.accept_req)
        self.b_reject = button("Reject", "danger", self.reject_req)
        self.b_resched = button("Propose new time", None, self.reschedule)
        self.b_confirm = button("Confirm new time", "primary", self.confirm_new)
        self.b_done = button("Mark completed", None, self.complete)
        self.b_fb = button("Leave feedback", "primary", self.feedback)
        for b in (self.b_accept, self.b_reject, self.b_resched, self.b_confirm, self.b_done, self.b_fb):
            row.addWidget(b)
        lay.addLayout(row)

    @property
    def role(self):
        return self.win.user["role"]

    @guarded
    def on_show(self):
        u = self.win.user
        stu = u["role"] == "Student"
        self.sub.setText("Your mentorship requests. Select a row to see the actions available for its status." if stu
                         else "Requests from students. Select a row to accept, reject or propose another time.")
        self.table.horizontalHeaderItem(1).setText("Alumnus" if stu else "Student")
        for b in (self.b_accept, self.b_reject, self.b_resched):
            b.setVisible(not stu)
        self.b_confirm.setVisible(stu)
        if stu:
            q = ("SELECT s.SessionID, a.Name, av.SlotDate, av.StartTime, av.EndTime, s.Status, s.Note FROM Session s "
                 "JOIN Alumnus a ON a.AlumniID = s.AlumniID JOIN Availability av ON av.AvailabilityID = s.AvailabilityID "
                 "WHERE s.StudentID = ? ORDER BY av.SlotDate DESC, av.StartTime")
        else:
            q = ("SELECT s.SessionID, st.Name, av.SlotDate, av.StartTime, av.EndTime, s.Status, s.Note FROM Session s "
                 "JOIN Student st ON st.StudentID = s.StudentID JOIN Availability av ON av.AvailabilityID = s.AvailabilityID "
                 "WHERE s.AlumniID = ? ORDER BY av.SlotDate DESC, av.StartTime")
        rows = self.db.query(q, (u["id"],))
        self.info = {r[0]: (fmt_date(r[2]), fmt_time(r[4]), r[5]) for r in rows}
        fill(self.table, [[r[0], r[1], fmt_date(r[2]), f"{fmt_time(r[3])} - {fmt_time(r[4])}", r[5], r[6]] for r in rows])
        self.update_buttons()

    def _past(self, sid):
        d, end, _ = self.info[sid]
        return datetime.datetime.strptime(f"{d} {end}", "%Y-%m-%d %H:%M") < datetime.datetime.now()

    @guarded
    def update_buttons(self, *_):
        sid = selected_id(self.table)
        status = self.info.get(sid, (None, None, None))[2] if sid is not None else None
        stu = self.role == "Student"
        self.b_accept.setEnabled(status == "Pending")
        self.b_reject.setEnabled(status == "Pending")
        self.b_resched.setEnabled(status == "Pending")
        self.b_confirm.setEnabled(status == "Rescheduled")
        self.b_done.setEnabled(status == "Confirmed" and self._past(sid))
        self.b_done.setToolTip("Available once the session time has passed")
        self.b_fb.setEnabled(status == "Completed")
        text = ""
        if sid is not None:
            rows = self.db.query("SELECT GivenBy, Rating, Comment FROM Feedback WHERE SessionID = ?", (sid,))
            given = {r[0]: r for r in rows}
            parts = []
            for who in ("Student", "Alumnus"):
                parts.append(f"{who}: {given[who][1]}/5 - {given[who][2] or 'no comment'}" if who in given else f"{who}: not given yet")
            text = "Feedback  |  " + "     |     ".join(parts)
        self.fb.setText(text)

    def _set_status(self, sid, status, free_slot=False):
        steps = []
        if free_slot:
            steps.append(("UPDATE Availability SET IsBooked = 0 WHERE AvailabilityID = (SELECT AvailabilityID FROM Session WHERE SessionID = ?)", (sid,)))
        steps.append(("UPDATE Session SET Status = ? WHERE SessionID = ?", (status, sid)))
        self.db.run(steps)
        self.on_show()

    @guarded
    def accept_req(self, *_):
        self._set_status(selected_id(self.table), "Confirmed")

    @guarded
    def reject_req(self, *_):
        if ask(self, "Reject this request? The time slot will become available again."):
            self._set_status(selected_id(self.table), "Rejected", free_slot=True)

    @guarded
    def confirm_new(self, *_):
        self._set_status(selected_id(self.table), "Confirmed")

    @guarded
    def complete(self, *_):
        self._set_status(selected_id(self.table), "Completed")

    @guarded
    def reschedule(self, *_):
        sid = selected_id(self.table)
        slots = self.db.query("SELECT AvailabilityID, SlotDate, StartTime, EndTime FROM Availability WHERE AlumniID = ? AND IsBooked = 0 AND SlotDate >= ? ORDER BY SlotDate, StartTime",
                              (self.win.user["id"], today()))
        if not slots:
            warn(self, "You have no free slots to offer. Add some on the Availability screen first.")
            return
        dlg = RescheduleDialog(self, [(r[0], fmt_date(r[1]), fmt_time(r[2]), fmt_time(r[3])) for r in slots])
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_slot = dlg.combo.currentData()
        self.db.run([
            ("UPDATE Availability SET IsBooked = 0 WHERE AvailabilityID = (SELECT AvailabilityID FROM Session WHERE SessionID = ?)", (sid,)),
            ("UPDATE Session SET AvailabilityID = ?, Status = 'Rescheduled' WHERE SessionID = ?", (new_slot, sid)),
            ("UPDATE Availability SET IsBooked = 1 WHERE AvailabilityID = ?", (new_slot,)),
        ])
        info(self, "New time proposed. The student now needs to confirm it.")
        self.on_show()

    @guarded
    def feedback(self, *_):
        sid = selected_id(self.table)
        dlg = FeedbackDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        giver = "Student" if self.role == "Student" else "Alumnus"
        try:
            self.db.execute("INSERT INTO Feedback (SessionID, GivenBy, Rating, Comment) VALUES (?,?,?,?)",
                            (sid, giver, int(dlg.rating.currentText()), dlg.comment.toPlainText().strip()))
        except DBError as e:
            if e.kind == "duplicate":
                warn(self, "You have already left feedback for this session.")
                return
            raise
        self.update_buttons()


# ============================================================================= Admin screens
class VerifyPage(Page):
    def __init__(self, win):
        super().__init__(win)
        lay = self.layout_with_title("Verify Alumni", "Approved alumni become visible to students. Rejected accounts cannot log in.")
        row = QHBoxLayout()
        self.filter = QComboBox(); self.filter.addItems(["Pending", "Approved", "Rejected", "All"])
        self.filter.currentIndexChanged.connect(self.on_show)
        row.addWidget(label("Show:", "muted")); row.addWidget(self.filter); row.addStretch()
        lay.addLayout(row)
        self.table = make_table(["ID", "Name", "Email", "Grad year", "Company", "Job title", "Industry", "Status"])
        lay.addWidget(self.table)
        r2 = QHBoxLayout()
        r2.addWidget(button("Approve", "primary", lambda: self.set("Approved")))
        r2.addWidget(button("Reject", "danger", lambda: self.set("Rejected")))
        lay.addLayout(r2)

    @guarded
    def on_show(self, *_):
        sql = "SELECT AlumniID, Name, Email, GraduationYear, Company, JobTitle, Industry, VerificationStatus FROM Alumnus"
        params = ()
        if self.filter.currentText() != "All":
            sql += " WHERE VerificationStatus = ?"; params = (self.filter.currentText(),)
        fill(self.table, [list(r) for r in self.db.query(sql + " ORDER BY Name", params)])

    @guarded
    def set(self, status):
        aid = selected_id(self.table)
        if aid is None:
            warn(self, "Select an alumnus first.")
            return
        self.db.execute("UPDATE Alumnus SET VerificationStatus = ?, VerifiedBy = ? WHERE AlumniID = ?", (status, self.win.user["id"], aid))
        self.on_show()


class TagPanel(QFrame):
    """One column of the taxonomy screen (Industry or Skill)."""

    def __init__(self, page, category):
        super().__init__()
        self.setObjectName("card")
        self.page, self.category = page, category
        v = QVBoxLayout(self)
        v.addWidget(label(f"{category} tags", "h2"))
        self.list = QListWidget(); v.addWidget(self.list)
        self.new = QLineEdit(); self.new.setPlaceholderText(f"New {category.lower()} name...")
        self.new.returnPressed.connect(self.add)
        v.addWidget(self.new)
        row = QHBoxLayout()
        row.addWidget(button("Add", "primary", self.add))
        row.addWidget(button("Rename", None, self.rename))
        row.addWidget(button("Remove", "danger", self.remove))
        v.addLayout(row)

    def reload(self):
        self.list.clear()
        for tid, name in self.page.db.query("SELECT TagID, TagName FROM Tag WHERE Category = ? ORDER BY TagName", (self.category,)):
            it = QListWidgetItem(name); it.setData(Qt.ItemDataRole.UserRole, tid); self.list.addItem(it)

    def _sel(self):
        it = self.list.currentItem()
        return (it.data(Qt.ItemDataRole.UserRole), it.text()) if it else (None, None)

    @guarded
    def add(self, *_):
        name = self.new.text().strip()
        if not name:
            return
        try:
            self.page.db.execute("INSERT INTO Tag (TagName, Category, CreatedBy) VALUES (?,?,?)", (name, self.category, self.page.win.user["id"]))
        except DBError as e:
            if e.kind == "duplicate":
                warn(self, f"'{name}' already exists in {self.category} tags.")
                return
            raise
        self.new.clear(); self.reload()

    @guarded
    def rename(self, *_):
        tid, old = self._sel()
        if tid is None:
            warn(self, "Select a tag first.")
            return
        new, ok = QInputDialog.getText(self, "Rename tag", "New name:", text=old)
        new = new.strip()
        if not ok or not new or new == old:
            return
        steps = [("UPDATE Tag SET TagName = ? WHERE TagID = ?", (new, tid))]
        if self.category == "Industry":
            steps.append(("UPDATE Alumnus SET Industry = ? WHERE Industry = ?", (new, old)))
        try:
            self.page.db.run(steps)
        except DBError as e:
            if e.kind == "duplicate":
                warn(self, f"'{new}' already exists.")
                return
            raise
        self.reload()

    @guarded
    def remove(self, *_):
        tid, name = self._sel()
        if tid is None:
            warn(self, "Select a tag first.")
            return
        db = self.page.db
        used = db.query("SELECT COUNT(*) FROM StudentInterest WHERE TagID = ?", (tid,))[0][0] + db.query("SELECT COUNT(*) FROM AlumniSkill WHERE TagID = ?", (tid,))[0][0]
        if self.category == "Industry":
            used += db.query("SELECT COUNT(*) FROM Alumnus WHERE Industry = ?", (name,))[0][0]
        if used and not ask(self, f"'{name}' is used by {used} profile(s). Removing it will remove it from those profiles. Continue?"):
            return
        steps = [("DELETE FROM StudentInterest WHERE TagID = ?", (tid,)), ("DELETE FROM AlumniSkill WHERE TagID = ?", (tid,))]
        if self.category == "Industry":
            steps.append(("UPDATE Alumnus SET Industry = NULL WHERE Industry = ?", (name,)))
        steps.append(("DELETE FROM Tag WHERE TagID = ?", (tid,)))
        db.run(steps)
        self.reload()


class TagsPage(Page):
    """SCREEN 7: Tag / industry management (setup screen 3)"""

    def __init__(self, win):
        super().__init__(win)
        lay = self.layout_with_title("Taxonomy Management", "Changes are saved to the database immediately. These tags are shared by students and alumni.")
        row = QHBoxLayout()
        self.industry = TagPanel(self, "Industry"); self.skill = TagPanel(self, "Skill")
        row.addWidget(self.industry); row.addWidget(self.skill)
        lay.addLayout(row)

    @guarded
    def on_show(self):
        self.industry.reload(); self.skill.reload()


class ReportsPage(Page):
    def __init__(self, win):
        super().__init__(win)
        lay = self.layout_with_title("Sessions & Engagement Reports", "Read-only view of every session on the platform.")
        row = QHBoxLayout()
        self.filter = QComboBox(); self.filter.addItems(["All", "Pending", "Confirmed", "Rejected", "Rescheduled", "Completed"])
        self.filter.currentIndexChanged.connect(self.on_show)
        row.addWidget(label("Status:", "muted")); row.addWidget(self.filter); row.addStretch()
        lay.addLayout(row)
        self.log = make_table(["ID", "Student", "Alumnus", "Date", "Time", "Status"])
        lay.addWidget(self.log, 3)
        bottom = QHBoxLayout()
        a = card(); al = QVBoxLayout(a); al.addWidget(label("Completed sessions per month", "h2"))
        self.monthly = make_table(["Month", "Sessions"]); al.addWidget(self.monthly)
        b = card(); bl = QVBoxLayout(b); bl.addWidget(label("Most requested alumni", "h2"))
        self.top = make_table(["Alumnus", "Requests"]); bl.addWidget(self.top)
        bottom.addWidget(a); bottom.addWidget(b)
        lay.addLayout(bottom, 2)

    @guarded
    def on_show(self, *_):
        sql = ("SELECT s.SessionID, st.Name, a.Name, av.SlotDate, av.StartTime, av.EndTime, s.Status FROM Session s "
               "JOIN Student st ON st.StudentID = s.StudentID JOIN Alumnus a ON a.AlumniID = s.AlumniID "
               "JOIN Availability av ON av.AvailabilityID = s.AvailabilityID")
        params = ()
        if self.filter.currentText() != "All":
            sql += " WHERE s.Status = ?"; params = (self.filter.currentText(),)
        rows = self.db.query(sql + " ORDER BY av.SlotDate DESC, av.StartTime", params)
        fill(self.log, [[r[0], r[1], r[2], fmt_date(r[3]), f"{fmt_time(r[4])} - {fmt_time(r[5])}", r[6]] for r in rows])
        months = {}
        for (d,) in self.db.query("SELECT av.SlotDate FROM Session s JOIN Availability av ON av.AvailabilityID = s.AvailabilityID WHERE s.Status = 'Completed'"):
            months[fmt_date(d)[:7]] = months.get(fmt_date(d)[:7], 0) + 1
        fill(self.monthly, [[m, n] for m, n in sorted(months.items())])
        top = self.db.query("SELECT a.Name, COUNT(*) FROM Session s JOIN Alumnus a ON a.AlumniID = s.AlumniID GROUP BY a.AlumniID, a.Name")
        top.sort(key=lambda r: -r[1])
        fill(self.top, [list(r) for r in top[:5]])


# ============================================================================= Main window
PAGES = [("login", LoginPage), ("register", RegisterPage), ("home", HomePage),
         ("s_profile", StudentProfilePage), ("s_search", SearchPage), ("s_book", BookingPage),
         ("sessions", SessionsPage), ("a_profile", AlumniProfilePage), ("a_avail", AvailabilityPage),
         ("ad_verify", VerifyPage), ("ad_tags", TagsPage), ("ad_reports", ReportsPage)]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.user = None
        self.current = None
        self.setWindowTitle("HamQadam - Alumni Mentorship & Career Network")
        self.resize(1120, 740)
        root = QWidget(); v = QVBoxLayout(root); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        self.setCentralWidget(root)
        if self.db.kind != "sqlserver":
            v.addWidget(label(f"Running on the OFFLINE practice database ({self.db.fallback_reason}). "
                              "Check SERVER in app/config.py and that you ran the SQL scripts in SSMS.", "banner"))
        header = QFrame(); header.setObjectName("header")
        self.header = header
        hl = QHBoxLayout(header); hl.setContentsMargins(18, 8, 18, 8)
        hl.addWidget(label("HamQadam", "brand"))
        self.nav = QHBoxLayout(); hl.addLayout(self.nav)
        hl.addStretch()
        self.who = QLabel(""); hl.addWidget(self.who)
        self.logout_btn = button("Logout", "nav", self.logout); hl.addWidget(self.logout_btn)
        v.addWidget(header)
        self.stack = QStackedWidget(); v.addWidget(self.stack)
        self.pages = {}
        for key, cls in PAGES:
            p = cls(self); self.pages[key] = p; self.stack.addWidget(p)
        self.statusBar().showMessage("Database: " + self.db.description)
        self.build_nav()
        self.go("login")

    def build_nav(self):
        while self.nav.count():
            w = self.nav.takeAt(0).widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        self.who.setText("")
        self.logout_btn.setVisible(self.user is not None)
        if not self.user:
            return
        self.who.setText(f"{self.user['name']}  ({self.user['role']})   ")
        self.nav_btns = {}
        items = [("Home", "home")] + NAV[self.user["role"]]
        for text, key in items:
            b = button(text, "nav", lambda _=False, k=key: self.go(k))
            self.nav.addWidget(b)
            self.nav_btns[key] = b

    def go(self, key):
        """Switch screen. This one function is all the 'navigation' in the app."""
        self.current = key
        page = self.pages[key]
        self.stack.setCurrentWidget(page)
        for k, b in getattr(self, "nav_btns", {}).items():
            try:
                b.setObjectName("navactive" if (k == key or (key == "s_book" and k == "s_search")) else "nav")
                b.style().unpolish(b); b.style().polish(b)
            except RuntimeError:
                pass
        page.on_show()

    def login_user(self, role, uid, name):
        self.user = {"role": role, "id": uid, "name": name}
        self.build_nav()
        self.go("home")

    def logout(self, *_):
        self.user = None
        self.nav_btns = {}
        self.build_nav()
        self.go("login")


def main():
    app = QApplication(sys.argv)
    if not PLAIN_LOOK:
        app.setStyleSheet(STYLE)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
