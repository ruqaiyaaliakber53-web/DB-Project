-- =====================================================================
-- HamQadam: Alumni Mentorship & Career Network System
-- SQL Server schema (run in SSMS: open this file, press F5)
-- 9 tables, matching the submitted ERD / relation schema
-- =====================================================================

IF DB_ID('HamQadam') IS NULL
    CREATE DATABASE HamQadam;
GO

USE HamQadam;
GO

-- Drop in reverse dependency order so the script can be re-run safely
DROP TABLE IF EXISTS Feedback;
DROP TABLE IF EXISTS Session;
DROP TABLE IF EXISTS Availability;
DROP TABLE IF EXISTS AlumniSkill;
DROP TABLE IF EXISTS StudentInterest;
DROP TABLE IF EXISTS Tag;
DROP TABLE IF EXISTS Alumnus;
DROP TABLE IF EXISTS Admin;
DROP TABLE IF EXISTS Student;
GO

-- ---------------------------------------------------------------------
-- Users
-- ---------------------------------------------------------------------
CREATE TABLE Student (
    StudentID       INT IDENTITY(1,1) PRIMARY KEY,
    Name            VARCHAR(100) NOT NULL,
    Email           VARCHAR(150) NOT NULL UNIQUE,
    Password        VARCHAR(100) NOT NULL,
    Batch           INT          NOT NULL,
    Major           VARCHAR(100) NOT NULL,
    IsEmailVerified BIT          NOT NULL DEFAULT 0
);

CREATE TABLE Admin (
    AdminID  INT IDENTITY(1,1) PRIMARY KEY,
    Name     VARCHAR(100) NOT NULL,
    Email    VARCHAR(150) NOT NULL UNIQUE,
    Password VARCHAR(100) NOT NULL
);

CREATE TABLE Alumnus (
    AlumniID           INT IDENTITY(1,1) PRIMARY KEY,
    Name               VARCHAR(100) NOT NULL,
    Email              VARCHAR(150) NOT NULL UNIQUE,
    Password           VARCHAR(100) NOT NULL,
    GraduationYear     INT          NOT NULL,
    Company            VARCHAR(100) NOT NULL,
    JobTitle           VARCHAR(100) NOT NULL,
    Industry           VARCHAR(100) NULL,
    Bio                VARCHAR(300) NULL,
    VerificationStatus VARCHAR(10)  NOT NULL DEFAULT 'Pending',
    VerifiedBy         INT          NULL,
    CONSTRAINT CK_Alumnus_Status CHECK (VerificationStatus IN ('Pending','Approved','Rejected')),
    CONSTRAINT FK_Alumnus_Admin  FOREIGN KEY (VerifiedBy) REFERENCES Admin(AdminID)
);

-- ---------------------------------------------------------------------
-- Shared taxonomy (industries + skills) and its junction tables
-- ---------------------------------------------------------------------
CREATE TABLE Tag (
    TagID     INT IDENTITY(1,1) PRIMARY KEY,
    TagName   VARCHAR(100) NOT NULL,
    Category  VARCHAR(10)  NOT NULL,
    CreatedBy INT          NULL,
    CONSTRAINT CK_Tag_Category CHECK (Category IN ('Industry','Skill')),
    CONSTRAINT UQ_Tag_Name_Category UNIQUE (TagName, Category),
    CONSTRAINT FK_Tag_Admin FOREIGN KEY (CreatedBy) REFERENCES Admin(AdminID)
);

CREATE TABLE StudentInterest (
    StudentID INT NOT NULL,
    TagID     INT NOT NULL,
    CONSTRAINT PK_StudentInterest PRIMARY KEY (StudentID, TagID),
    CONSTRAINT FK_SI_Student FOREIGN KEY (StudentID) REFERENCES Student(StudentID),
    CONSTRAINT FK_SI_Tag     FOREIGN KEY (TagID)     REFERENCES Tag(TagID)
);

CREATE TABLE AlumniSkill (
    AlumniID INT NOT NULL,
    TagID    INT NOT NULL,
    CONSTRAINT PK_AlumniSkill PRIMARY KEY (AlumniID, TagID),
    CONSTRAINT FK_AS_Alumnus FOREIGN KEY (AlumniID) REFERENCES Alumnus(AlumniID),
    CONSTRAINT FK_AS_Tag     FOREIGN KEY (TagID)    REFERENCES Tag(TagID)
);

-- ---------------------------------------------------------------------
-- Availability slots offered by alumni
-- ---------------------------------------------------------------------
CREATE TABLE Availability (
    AvailabilityID INT IDENTITY(1,1) PRIMARY KEY,
    AlumniID       INT     NOT NULL,
    SlotDate       DATE    NOT NULL,
    StartTime      TIME(0) NOT NULL,
    EndTime        TIME(0) NOT NULL,
    IsBooked       BIT     NOT NULL DEFAULT 0,
    CONSTRAINT CK_Avail_Times CHECK (EndTime > StartTime),
    CONSTRAINT FK_Avail_Alumnus FOREIGN KEY (AlumniID) REFERENCES Alumnus(AlumniID)
);

-- ---------------------------------------------------------------------
-- Session = the transaction table (request -> confirm -> complete)
-- ---------------------------------------------------------------------
CREATE TABLE Session (
    SessionID      INT IDENTITY(1,1) PRIMARY KEY,
    StudentID      INT          NOT NULL,
    AlumniID       INT          NOT NULL,
    AvailabilityID INT          NOT NULL,
    Status         VARCHAR(12)  NOT NULL DEFAULT 'Pending',
    Note           VARCHAR(500) NULL,
    RequestedAt    DATETIME     NOT NULL DEFAULT GETDATE(),
    CONSTRAINT CK_Session_Status CHECK (Status IN ('Pending','Confirmed','Rejected','Rescheduled','Completed')),
    CONSTRAINT FK_Session_Student FOREIGN KEY (StudentID)      REFERENCES Student(StudentID),
    CONSTRAINT FK_Session_Alumnus FOREIGN KEY (AlumniID)       REFERENCES Alumnus(AlumniID),
    CONSTRAINT FK_Session_Avail   FOREIGN KEY (AvailabilityID) REFERENCES Availability(AvailabilityID)
);

-- A slot can belong to only ONE active session at a time (prevents double booking).
-- Rejected sessions release their slot, so they are excluded from the rule.
CREATE UNIQUE INDEX UX_Session_ActiveSlot
    ON Session(AvailabilityID)
    WHERE Status IN ('Pending','Confirmed','Rescheduled','Completed');

-- ---------------------------------------------------------------------
-- Feedback: max one row per participant per session
-- ---------------------------------------------------------------------
CREATE TABLE Feedback (
    FeedbackID INT IDENTITY(1,1) PRIMARY KEY,
    SessionID  INT          NOT NULL,
    GivenBy    VARCHAR(10)  NOT NULL,
    Rating     INT          NOT NULL,
    Comment    VARCHAR(500) NULL,
    CONSTRAINT CK_Feedback_GivenBy CHECK (GivenBy IN ('Student','Alumnus')),
    CONSTRAINT CK_Feedback_Rating  CHECK (Rating BETWEEN 1 AND 5),
    CONSTRAINT UQ_Feedback_Session_Giver UNIQUE (SessionID, GivenBy),
    CONSTRAINT FK_Feedback_Session FOREIGN KEY (SessionID) REFERENCES Session(SessionID)
);
GO
