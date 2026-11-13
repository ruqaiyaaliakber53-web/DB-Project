-- =====================================================================
-- HamQadam sample data (all fake). Run AFTER 01_schema.sql.
-- Demo logins (password for everyone: pass123)
--   Student : sara.ahmed@st.habib.edu.pk
--   Alumnus : zara.qureshi@alumni.habib.edu.pk
--   Admin   : admin@habib.edu.pk
-- =====================================================================
USE HamQadam;

INSERT INTO Admin (Name, Email, Password) VALUES
('Career Office Admin', 'admin@habib.edu.pk', 'pass123');

INSERT INTO Student (Name, Email, Password, Batch, Major, IsEmailVerified) VALUES
('Sara Ahmed',   'sara.ahmed@st.habib.edu.pk',   'pass123', 2028, 'Computer Science',            1),
('Bilal Hussain','bilal.hussain@st.habib.edu.pk','pass123', 2027, 'Electrical Engineering',      1),
('Hira Raza',    'hira.raza@st.habib.edu.pk',    'pass123', 2029, 'Computer Science',            1),
('Omar Farooq',  'omar.farooq@st.habib.edu.pk',  'pass123', 2028, 'Social Development and Policy',1);

INSERT INTO Alumnus (Name, Email, Password, GraduationYear, Company, JobTitle, Industry, Bio, VerificationStatus, VerifiedBy) VALUES
('Zara Qureshi',    'zara.qureshi@alumni.habib.edu.pk',  'pass123', 2021, 'Nexa Systems',      'Software Engineer',     'Software Engineering', 'Backend engineer. Happy to talk about internships, interviews and breaking into tech.', 'Approved', 1),
('Faizan Ali',      'faizan.ali@alumni.habib.edu.pk',    'pass123', 2020, 'Crescent Capital',  'Financial Analyst',     'Finance',              'Equity research and financial modelling. Can review your CV for finance roles.',        'Approved', 1),
('Maryam Siddiqui', 'maryam.siddiqui@alumni.habib.edu.pk','pass123', 2019, 'Indus Advisory',    'Management Consultant', 'Consulting',           'Consulting case prep, networking and career switching advice.',                        'Approved', 1),
('Hamza Sheikh',    'hamza.sheikh@alumni.habib.edu.pk',  'pass123', 2022, 'Metric Labs',       'Data Scientist',        'Software Engineering', 'Machine learning and analytics. Ask me about grad school applications too.',           'Approved', 1),
('Ayesha Noor',     'ayesha.noor@alumni.habib.edu.pk',   'pass123', 2018, 'Orbit Health',      'Product Manager',       'Healthcare',           'Product management in health tech.',                                                    'Approved', 1),
('Daniyal Mirza',   'daniyal.mirza@alumni.habib.edu.pk', 'pass123', 2021, 'BrightPath Academy','Curriculum Lead',       'Education',            'Education sector, teaching and curriculum design.',                                     'Approved', 1),
('Sana Rahim',      'sana.rahim@alumni.habib.edu.pk',    'pass123', 2020, 'Lumen Media',       'Marketing Manager',     'Marketing',            'Brand and digital marketing.',                                                          'Approved', 1),
('Usman Tariq',     'usman.tariq@alumni.habib.edu.pk',   'pass123', 2023, 'Pulse Analytics',   'Junior Analyst',        'Finance',              'Recently graduated, waiting for verification.',                                         'Pending',  NULL);

-- Industry tags (ids 1-6) then Skill tags (ids 7-16)
INSERT INTO Tag (TagName, Category, CreatedBy) VALUES
('Software Engineering','Industry',1), ('Finance','Industry',1), ('Consulting','Industry',1),
('Healthcare','Industry',1), ('Education','Industry',1), ('Marketing','Industry',1),
('Python','Skill',1), ('Data Analysis','Skill',1), ('Machine Learning','Skill',1),
('Financial Modeling','Skill',1), ('Public Speaking','Skill',1), ('Project Management','Skill',1),
('SQL','Skill',1), ('UI/UX Design','Skill',1), ('Research','Skill',1), ('Leadership','Skill',1);

INSERT INTO StudentInterest (StudentID, TagID) VALUES
(1,1),(1,7),(1,9),
(2,2),(2,10),
(3,1),(3,14),(3,8),
(4,4),(4,15);

INSERT INTO AlumniSkill (AlumniID, TagID) VALUES
(1,7),(1,13),(1,9),(1,12),
(2,10),(2,8),(2,16),
(3,12),(3,11),(3,16),(3,15),
(4,7),(4,8),(4,9),(4,13),
(5,12),(5,16),(5,15),
(6,11),(6,16),(6,15),
(7,11),(7,14),(7,12),
(8,8),(8,10);

-- Availability (ids 1-16 in this order)
INSERT INTO Availability (AlumniID, SlotDate, StartTime, EndTime, IsBooked) VALUES
(1,'2026-11-02','10:00','10:30',1),  -- 1  completed session
(2,'2026-11-03','15:00','15:30',1),  -- 2  completed session
(1,'2026-11-05','11:00','11:30',1),  -- 3  confirmed, already in the past (can be marked completed)
(3,'2026-11-17','14:00','14:30',1),  -- 4  pending request
(1,'2026-11-17','16:00','16:30',1),  -- 5  confirmed, in the future
(2,'2026-11-18','10:00','10:30',0),  -- 6  was rejected, slot released
(2,'2026-11-19','12:00','12:30',0),  -- 7
(3,'2026-11-18','09:00','09:30',0),  -- 8
(4,'2026-11-16','13:00','13:30',0),  -- 9
(4,'2026-11-20','13:00','13:30',0),  -- 10
(5,'2026-11-19','17:00','17:30',0),  -- 11
(6,'2026-11-18','11:00','11:30',0),  -- 12
(7,'2026-11-20','15:00','15:30',0),  -- 13
(1,'2026-11-19','10:00','10:30',0),  -- 14
(3,'2026-11-16','09:00','09:30',0),  -- 15
(5,'2026-11-21','10:00','10:30',1);  -- 16 rescheduled session

INSERT INTO Session (StudentID, AlumniID, AvailabilityID, Status, Note, RequestedAt) VALUES
(1,1, 1,'Completed',  'Advice on landing a software engineering internship.', '2026-10-28T09:15:00'),
(2,2, 2,'Completed',  'How do I get into equity research?',                   '2026-10-29T14:20:00'),
(3,1, 3,'Confirmed',  'Portfolio review and interview tips.',                 '2026-10-30T11:05:00'),
(1,3, 4,'Pending',    'Would like to understand consulting recruitment.',     '2026-11-10T16:40:00'),
(2,1, 5,'Confirmed',  'Switching from electrical engineering to software.',   '2026-11-08T10:10:00'),
(4,5,16,'Rescheduled','Interested in health-tech product roles.',             '2026-11-09T13:30:00'),
(3,2, 6,'Rejected',   'Quick question about financial modelling.',            '2026-11-07T12:00:00');

INSERT INTO Feedback (SessionID, GivenBy, Rating, Comment) VALUES
(1,'Student',5,'Very practical advice, thank you!'),
(1,'Alumnus',4,'Motivated student with good questions.'),
(2,'Student',4,'Helpful overview of the finance path.');
