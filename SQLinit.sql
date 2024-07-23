-- Drop tables if they exist
DROP TABLE IF EXISTS Matches;
DROP TABLE IF EXISTS UserSwipes;
DROP TABLE IF EXISTS UserSkills;
DROP TABLE IF EXISTS Skills;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS PotentialUsers;

-- Create Users table
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL
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
INSERT INTO Skills (skill_name) VALUES ('C#'), ('Python'), ('MySQL');
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

-- Create Trigger
DELIMITER //

CREATE TRIGGER check_match AFTER INSERT ON UserSwipes
FOR EACH ROW
BEGIN
    IF NEW.swipe_type = 'like' THEN
        DECLARE match_exists INT;
        SELECT COUNT(*) INTO match_exists
        FROM UserSwipes
        WHERE swiper_id = NEW.swipee_id
        AND swipee_id = NEW.swiper_id
        AND swipe_type = 'like';

        IF match_exists > 0 THEN
            INSERT INTO Matches (user1_id, user2_id) VALUES (LEAST(NEW.swiper_id, NEW.swipee_id), GREATEST(NEW.swiper_id, NEW.swipee_id));
        END IF;
    END IF;
END //

DELIMITER ;

SELECT * FROM UserSwipes;