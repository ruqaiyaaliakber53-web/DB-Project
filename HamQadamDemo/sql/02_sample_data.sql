-- sample data

use HamQadam;

INSERT INTO Admin (Name, Email, Password) VALUES
('Career Office Admin', 'admin@habib.edu.pk', 'pass123');

INSERT INTO Student (Name, Email, Password, Batch, Major, IsEmailVerified) VALUES
('Sara Ahmed', 'sara.ahmed@st.habib.edu.pk', 'pass123', 2028, 'Computer Science', 1),
('Bilal Hussain', 'bilal.hussain@st.habib.edu.pk', 'pass123', 2027, 'Electrical Engineering',1),
('Hira Raza', 'hira.raza@st.habib.edu.pk','pass123', 2029, 'Computer Science',1);

INSERT INTO Alumnus (Name, Email, Password, GraduationYear, Company, JobTitle, Industry, Bio, VerificationStatus, VerifiedBy) VALUES
('Zara qureshi',    'zara.qureshi@alumni.habib.edu.pk',    'pass123', 2021, 'Nexa Systems',     'Software Engineer',     'Software Engineering', 'Backend engineer. Happy to talk about internships and interviews.', 'Approved', 1),
('Faizan Ali',      'faizan.ali@alumni.habib.edu.pk',      'pass123', 2020, 'Crescent Capital', 'Financial Analyst',     'Finance',              'Equity research and financial modelling.',                          'Approved', 1),
('Maryam Siddiqui', 'maryam.siddiqui@alumni.habib.edu.pk', 'pass123', 2019, 'Indus Advisory',   'Management Consultant', 'Consulting',           'Consulting case prep and career advice.',                           'Approved', 1),
('Usman Tariq',     'usman.tariq@alumni.habib.edu.pk',     'pass123', 2023, 'Pulse Analytics',  'Junior Analyst',        'Finance',              'Waiting for verification.',                                         'Pending',  NULL);

INSERT INTO Tag (TagName, Category, CreatedBy) VALUES
('Software Engineering','Industry',1), ('Finance','Industry',1), ('Consulting','Industry',1),
('Python','Skill',1), ('Data Analysis','Skill',1), ('Financial Modeling','Skill',1);

INSERT INTO StudentInterest (StudentID, TagID) VALUES (1,1),(1,4),(2,2),(3,1);

INSERT INTO AlumniSkill (AlumniID, TagID) VALUES (1,4),(2,6),(2,5),(3,5);

INSERT INTO Availability (AlumniID, SlotDate, StartTime, EndTime, IsBooked) VALUES
(1,'2026-11-17','10:00','10:30',1),  -- 1 pending session
(1,'2026-11-18','14:00','14:30',0),  -- 2 free
(2,'2026-11-19','11:00','11:30',1),  -- 3 confirmed session
(3,'2026-11-20','15:00','15:30',0),  -- 4 free
(1,'2026-11-02','10:00','10:30',1);  -- 5 completed session

INSERT INTO Session (StudentID, AlumniID, AvailabilityID, Status, Note, RequestedAt) VALUES
(1,1,5,'Completed','Advice on landing a software engineering internship.','2026-10-28T09:15:00'),
(2,2,3,'Confirmed','How do I get into equity research?',                   '2026-11-08T10:10:00'),
(3,1,1,'Pending',  'Portfolio review and interview tips.',                 '2026-11-10T16:40:00');

INSERT INTO Feedback (SessionID, GivenBy, Rating, Comment) VALUES
(1,'Student',5,'Very helpful, thank you!');
