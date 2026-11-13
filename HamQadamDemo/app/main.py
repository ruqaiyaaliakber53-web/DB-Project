"""
HamQadam - interim demo (UI mockup).
All screens are created and linked together; buttons move between screens.
The data in the tables here is just for show - the real data lives in SQL Server (open it in SSMS).

Run:  python main.py
"""
import sys
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox, QPushButton, QStackedWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import Qt

# which screens each role can open from the top bar  (label, page name)
NAV = {
    "Student": [("Find Alumni", "search"), ("My Sessions", "sessions")],
    "Alumnus": [("My Profile", "profile"), ("My Availability", "availability"), ("Session Requests", "requests")],
    "Admin":   [("Verify Alumni", "verify"), ("Manage Tags", "tags")],
}
FIRST_PAGE = {"Student": "search", "Alumnus": "profile", "Admin": "verify"}


def make_table(headers, rows):
    t = QTableWidget(len(rows), len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            t.setItem(r, c, QTableWidgetItem(str(v)))
    return t


def add_row(t, row):
    r = t.rowCount()
    t.insertRow(r)
    for c, v in enumerate(row):
        t.setItem(r, c, QTableWidgetItem(str(v)))


def set_status(t, col, text):
    """Change the Status cell of the selected row."""
    r = t.currentRow()
    if r < 0:
        QMessageBox.information(t, "HamQadam", "Select a row first.")
        return
    t.item(r, col).setText(text)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HamQadam - Alumni Mentorship & Career Network System")
        self.resize(1000, 650)
        self.role = None
        root = QWidget()
        self.setCentralWidget(root)
        v = QVBoxLayout(root)
        self.nav = QHBoxLayout()          # top bar with buttons for the current role
        v.addLayout(self.nav)
        self.stack = QStackedWidget()     # a pile of screens; only one is visible at a time
        v.addWidget(self.stack)
        self.pages = {}
        self.build_pages()
        self.go("login")

    # ---- navigation: this one function is how every screen links to another ----
    def go(self, name):
        self.stack.setCurrentWidget(self.pages[name])

    def login_as(self, role):
        self.role = role
        while self.nav.count():
            w = self.nav.takeAt(0).widget()
            if w:
                w.setParent(None)
        for text, page in NAV[role]:
            self.nav.addWidget(self.button(text, lambda _=False, p=page: self.go(p)))
        self.nav.addStretch()
        self.nav.addWidget(QLabel(f"Signed in as {role}"))
        self.nav.addWidget(self.button("Logout", self.logout))
        self.go(FIRST_PAGE[role])

    def logout(self, *_):
        self.role = None
        while self.nav.count():
            w = self.nav.takeAt(0).widget()
            if w:
                w.setParent(None)
        self.go("login")

    # ---- small helpers ----
    def button(self, text, fn):
        b = QPushButton(text)
        b.clicked.connect(fn)
        return b

    def new_page(self, name, title):
        page = QWidget()
        lay = QVBoxLayout(page)
        head = QLabel(title)
        head.setStyleSheet("font-size: 18px; font-weight: bold;")
        lay.addWidget(head)
        self.pages[name] = page
        self.stack.addWidget(page)
        return lay

    def say(self, msg):
        QMessageBox.information(self, "HamQadam", msg)

    # ------------------------------------------------------------------ the screens
    def build_pages(self):
        self.page_login()
        self.page_register()
        self.page_search()
        self.page_booking()
        self.page_sessions()
        self.page_feedback()
        self.page_profile()
        self.page_availability()
        self.page_requests()
        self.page_verify()
        self.page_tags()

    def page_login(self):                                    # Screen 1
        lay = self.new_page("login", "HamQadam - Login")
        form = QFormLayout()
        role = QComboBox(); role.addItems(["Student", "Alumnus", "Admin"])
        email = QLineEdit(); pw = QLineEdit(); pw.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("I am a", role); form.addRow("Email", email); form.addRow("Password", pw)
        lay.addLayout(form)
        lay.addWidget(self.button("Login", lambda: self.login_as(role.currentText())))
        lay.addWidget(self.button("Register a new account", lambda: self.go("register")))
        lay.addStretch()

    def page_register(self):                                 # Screen 1 (registration)
        lay = self.new_page("register", "Register")
        form = QFormLayout()
        role = QComboBox(); role.addItems(["Student", "Alumnus"])
        for label, w in [("Register as", role), ("Name", QLineEdit()), ("Email", QLineEdit()),
                         ("Password", QLineEdit()), ("Batch / Graduation year", QLineEdit()),
                         ("Major / Company", QLineEdit())]:
            form.addRow(label, w)
        lay.addLayout(form)

        def submit():
            self.say("Account created. (Alumni accounts stay 'Pending' until an admin approves them.)")
            self.go("login")
        lay.addWidget(self.button("Register", submit))
        lay.addWidget(self.button("Back to login", lambda: self.go("login")))
        lay.addStretch()

    def page_search(self):                                   # Screen 4: search & discovery
        lay = self.new_page("search", "Find Alumni")
        row = QHBoxLayout()
        name = QLineEdit(); name.setPlaceholderText("Search by name...")
        industry = QComboBox(); industry.addItems(["All industries", "Software Engineering", "Finance", "Consulting"])
        row.addWidget(name); row.addWidget(industry)
        lay.addLayout(row)
        data = [("Zara Qureshi", "Software Engineer", "Nexa Systems", "Software Engineering", "Python"),
                ("Faizan Ali", "Financial Analyst", "Crescent Capital", "Finance", "Financial Modeling, Data Analysis"),
                ("Maryam Siddiqui", "Management Consultant", "Indus Advisory", "Consulting", "Data Analysis")]
        self.search_table = make_table(["Name", "Job title", "Company", "Industry", "Skills"], data)
        lay.addWidget(self.search_table)

        def do_search():
            for r, d in enumerate(data):
                ok = name.text().lower() in d[0].lower() and (industry.currentIndex() == 0 or d[3] == industry.currentText())
                self.search_table.setRowHidden(r, not ok)
        row.addWidget(self.button("Search", do_search))

        def view():
            r = self.search_table.currentRow()
            if r < 0:
                self.say("Select an alumnus first.")
                return
            self.booking_who.setText("Booking a session with: " + data[r][0] + "  (" + data[r][1] + ", " + data[r][2] + ")")
            self.go("booking")
        lay.addWidget(self.button("View profile and book a session", view))

    def page_booking(self):                                  # Screen 5: transaction screen
        lay = self.new_page("booking", "Book a Mentorship Session")
        self.booking_who = QLabel("")
        lay.addWidget(self.booking_who)
        lay.addWidget(QLabel("Available slots:"))
        slots = make_table(["Date", "Start", "End"], [("2026-11-18", "14:00", "14:30"), ("2026-11-20", "15:00", "15:30")])
        lay.addWidget(slots)
        lay.addWidget(QLabel("What would you like to discuss?"))
        note = QTextEdit(); note.setMaximumHeight(80)
        lay.addWidget(note)

        def submit():
            r = slots.currentRow()
            if r < 0:
                self.say("Please select a time slot.")
                return
            add_row(self.sessions_table, (4, self.booking_who.text().split(": ")[1].split("  (")[0],
                                          slots.item(r, 0).text(), slots.item(r, 1).text(), "Pending"))
            self.say("Request sent. Status: Pending.")
            self.go("sessions")
        lay.addWidget(self.button("Submit session request", submit))
        lay.addWidget(self.button("Back to search", lambda: self.go("search")))

    def page_sessions(self):                                 # Screen 6: session management (student)
        lay = self.new_page("sessions", "My Sessions")
        self.sessions_table = make_table(["ID", "Alumnus", "Date", "Time", "Status"],
                                         [(1, "Zara Qureshi", "2026-11-02", "10:00", "Completed"),
                                          (2, "Faizan Ali", "2026-11-19", "11:00", "Confirmed"),
                                          (3, "Zara Qureshi", "2026-11-17", "10:00", "Pending")])
        lay.addWidget(self.sessions_table)
        row = QHBoxLayout()
        row.addWidget(self.button("Mark completed", lambda: set_status(self.sessions_table, 4, "Completed")))
        row.addWidget(self.button("Leave feedback", lambda: self.go("feedback")))
        lay.addLayout(row)

    def page_feedback(self):                                 # Screen 6: feedback
        lay = self.new_page("feedback", "Leave Feedback")
        form = QFormLayout()
        rating = QComboBox(); rating.addItems(["5", "4", "3", "2", "1"])
        comment = QTextEdit(); comment.setMaximumHeight(100)
        form.addRow("Rating (1-5)", rating); form.addRow("Comment", comment)
        lay.addLayout(form)

        def submit():
            self.say("Thank you for your feedback!")
            self.go("sessions")
        lay.addWidget(self.button("Submit feedback", submit))
        lay.addWidget(self.button("Back", lambda: self.go("sessions")))
        lay.addStretch()

    def page_profile(self):                                  # Screen 2: profile & expertise setup
        lay = self.new_page("profile", "My Profile & Expertise")
        form = QFormLayout()
        industry = QComboBox(); industry.addItems(["Software Engineering", "Finance", "Consulting"])
        bio = QTextEdit(); bio.setMaximumHeight(80)
        form.addRow("Company", QLineEdit("Nexa Systems")); form.addRow("Job title", QLineEdit("Software Engineer"))
        form.addRow("Industry", industry); form.addRow("Short bio", bio)
        lay.addLayout(form)
        lay.addWidget(QLabel("Skills (select any):"))
        skills = QListWidget(); skills.addItems(["Python", "Data Analysis", "Financial Modeling"])
        skills.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        lay.addWidget(skills)
        lay.addWidget(self.button("Save profile", lambda: self.say("Profile saved.")))

    def page_availability(self):                             # Screen 3: availability configuration
        lay = self.new_page("availability", "My Availability")
        row = QHBoxLayout()
        d, s, e = QLineEdit("2026-11-21"), QLineEdit("10:00"), QLineEdit("10:30")
        for lbl, w in (("Date", d), ("Start", s), ("End", e)):
            row.addWidget(QLabel(lbl)); row.addWidget(w)
        lay.addLayout(row)
        t = make_table(["Date", "Start", "End", "Status"],
                       [("2026-11-17", "10:00", "10:30", "Booked"), ("2026-11-18", "14:00", "14:30", "Free")])
        lay.addWidget(t)
        row.addWidget(self.button("Add slot", lambda: add_row(t, (d.text(), s.text(), e.text(), "Free"))))

    def page_requests(self):                                 # Screen 6: session management (alumnus)
        lay = self.new_page("requests", "Session Requests")
        t = make_table(["ID", "Student", "Date", "Time", "Status"],
                       [(3, "Hira Raza", "2026-11-17", "10:00", "Pending"),
                        (1, "Sara Ahmed", "2026-11-02", "10:00", "Completed")])
        lay.addWidget(t)
        row = QHBoxLayout()
        row.addWidget(self.button("Accept", lambda: set_status(t, 4, "Confirmed")))
        row.addWidget(self.button("Reject", lambda: set_status(t, 4, "Rejected")))
        row.addWidget(self.button("Propose new time", lambda: set_status(t, 4, "Rescheduled")))
        row.addWidget(self.button("Leave feedback", lambda: self.go("feedback")))
        lay.addLayout(row)

    def page_verify(self):                                   # admin: verify alumni
        lay = self.new_page("verify", "Verify Alumni")
        t = make_table(["Name", "Email", "Company", "Status"],
                       [("Usman Tariq", "usman.tariq@alumni.habib.edu.pk", "Pulse Analytics", "Pending")])
        lay.addWidget(t)
        row = QHBoxLayout()
        row.addWidget(self.button("Approve", lambda: set_status(t, 3, "Approved")))
        row.addWidget(self.button("Reject", lambda: set_status(t, 3, "Rejected")))
        lay.addLayout(row)

    def page_tags(self):                                     # Screen 7: tag / taxonomy management
        lay = self.new_page("tags", "Taxonomy Management")
        for title, items in (("Industry tags", ["Software Engineering", "Finance", "Consulting"]),
                             ("Skill tags", ["Python", "Data Analysis", "Financial Modeling"])):
            lay.addWidget(QLabel(title))
            lst = QListWidget(); lst.addItems(items)
            lay.addWidget(lst)
            row = QHBoxLayout()
            new = QLineEdit(); new.setPlaceholderText("New name...")
            row.addWidget(new)
            row.addWidget(self.button("Add", lambda _=False, l=lst, n=new: (n.text() and l.addItem(n.text()), n.clear())))
            row.addWidget(self.button("Remove", lambda _=False, l=lst: l.takeItem(l.currentRow()) if l.currentRow() >= 0 else None))
            lay.addLayout(row)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    sys.exit(app.exec())
