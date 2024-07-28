DROP TABLE IF EXISTS Messages;
DROP TABLE IF EXISTS DailySwipes;
DROP TABLE IF EXISTS PotentialJobs;
DROP TABLE IF EXISTS RecruiteePreferences;
DROP TABLE IF EXISTS RecruiteeCities;
DROP TABLE IF EXISTS Jobs;
DROP TABLE IF EXISTS Recruitee;
DROP TABLE IF EXISTS Location;
DROP TABLE IF EXISTS Matches;
DROP TABLE IF EXISTS PotentialUsers;
DROP TABLE IF EXISTS UserSwipes;
DROP TABLE IF EXISTS UserSkills;
DROP TABLE IF EXISTS Skills;
DROP TABLE IF EXISTS Users;

-- Create Users table
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    user_type ENUM('recruiter', 'recruitee', 'recruiter_premium', 'recruitee_premium') NOT NULL
);

-- Create Skills table
CREATE TABLE Skills (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL
);

-- Create UserSkills table
CREATE TABLE UserSkills (
    user_skill_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    skill_id INT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (skill_id) REFERENCES Skills(skill_id)
);

-- Create UserSwipes table
CREATE TABLE UserSwipes (
    swipe_id INT AUTO_INCREMENT PRIMARY KEY,
    swiper_id INT,
    swipee_id INT,
    swipe_type ENUM('like', 'dislike'),
    FOREIGN KEY (swiper_id) REFERENCES Users(user_id),
    FOREIGN KEY (swipee_id) REFERENCES Users(user_id)
);

-- Create PotentialUsers table
CREATE TABLE PotentialUsers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    filterer_id INT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (filterer_id) REFERENCES Users(user_id)
);

-- Create Matches table
CREATE TABLE Matches (
    match_id INT AUTO_INCREMENT PRIMARY KEY,
    user1_id INT,
    user2_id INT,
    FOREIGN KEY (user1_id) REFERENCES Users(user_id),
    FOREIGN KEY (user2_id) REFERENCES Users(user_id)
);

-- Create Location table
CREATE TABLE Location (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL
);

-- Create Recruitee table
CREATE TABLE Recruitee (
    recruitee_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    bio TEXT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- Create RecruiteeCities table
CREATE TABLE RecruiteeCities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    location_id INT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (location_id) REFERENCES Location(location_id)
);

-- Create RecruiteePreferences table
CREATE TABLE RecruiteePreferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    min_compensation INT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- Create Jobs table
CREATE TABLE Jobs (
    job_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    job_title TINYTEXT, 
    job_description TEXT,
    compensation INT,
    job_location INT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (job_location) REFERENCES Location(location_id)
);

-- Create PotentialJobs table
CREATE TABLE PotentialJobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT,
    filterer_id INT,
    FOREIGN KEY (job_id) REFERENCES Jobs(job_id),
    FOREIGN KEY (filterer_id) REFERENCES Users(user_id)
);

-- Create DailySwipes table
CREATE TABLE DailySwipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    swipe_date DATE,
    swipe_count INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    UNIQUE(user_id, swipe_date)
);

-- Create Messages table
CREATE TABLE Messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT,
    receiver_id INT,
    message_text TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES Users(user_id),
    FOREIGN KEY (receiver_id) REFERENCES Users(user_id)
);

-- Insert initial skills
INSERT INTO Skills (skill_name) VALUES ('LISP'), ('Docker'), ('Kubernetes'), ('Flask');

-- Insert initial locations
INSERT INTO Location (location_name) VALUES ('New York'), ('San Francisco'), ('Los Angeles'), ('Chicago'), ('Houston'), ('Miami'), ('Seattle'), ('Boston'), ('Denver'), ('Austin');

-- Trigger to check for match
DELIMITER //

CREATE TRIGGER check_for_match
AFTER INSERT ON UserSwipes
FOR EACH ROW
BEGIN
    DECLARE match_exists INT DEFAULT 0;
    IF NEW.swipe_type = 'like' THEN
        SELECT COUNT(*) INTO match_exists
        FROM UserSwipes
        WHERE swiper_id = NEW.swipee_id
        AND swipee_id = NEW.swiper_id
        AND swipe_type = 'like';

        IF match_exists > 0 THEN
            INSERT INTO Matches (user1_id, user2_id) 
            VALUES (LEAST(NEW.swiper_id, NEW.swipee_id), GREATEST(NEW.swiper_id, NEW.swipee_id));
        END IF;
    END IF;
END //

DELIMITER ;

-- Disable safe updates for deletion
SET SQL_SAFE_UPDATES = 0;
DELETE FROM UserSwipes;
SET SQL_SAFE_UPDATES = 1;

-- Show triggers
SHOW TRIGGERS;
