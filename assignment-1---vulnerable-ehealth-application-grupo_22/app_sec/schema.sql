-- MySQL Workbench Forward Engineering

-- SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
-- SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
-- SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema clinic
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema clinic
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS clinic;
CREATE SCHEMA IF NOT EXISTS `clinic` DEFAULT CHARACTER SET latin1 ;
USE `clinic` ;

-- -----------------------------------------------------
-- Table `clinic`.`departments`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `clinic`.`departments` (
  `id` INT NOT NULL,
  `name` VARCHAR(45) NOT NULL,
  `description` VARCHAR(1000) NULL DEFAULT NULL,
  `url_photo` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `clinic`.`doctors`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `clinic`.`doctors` (
  `id` INT NOT NULL,
  `first_name` VARCHAR(45) NOT NULL,
  `last_name` VARCHAR(45) NOT NULL,
  `description` VARCHAR(1000) NULL DEFAULT NULL,
  `url_photo` VARCHAR(45) NULL DEFAULT NULL,
  `id_department` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_doctor_department_idx` (`id_department` ASC),
  CONSTRAINT `fk_doctor_department`
    FOREIGN KEY (`id_department`)
    REFERENCES `clinic`.`departments` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `clinic`.`users`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `clinic`.`users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(45) NOT NULL,
  `password` VARCHAR(512) NOT NULL,
  `first_name` VARCHAR(45) NOT NULL,
  `last_name` VARCHAR(45) NOT NULL,
  `phone` CHAR(9) NOT NULL,
  `email` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `clinic`.`appointments`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `clinic`.`appointments` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `message` VARCHAR(1000) NOT NULL,
  `start_date` DATETIME NOT NULL,
  `end_date` DATETIME NOT NULL,
  `id_doctor` INT NOT NULL,
  `id_user` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_appointment_doctor_idx` (`id_doctor` ASC),
  INDEX `fk_appointment_user_idx` (`id_user` ASC),
  CONSTRAINT `fk_appointment_doctor`
    FOREIGN KEY (`id_doctor`)
    REFERENCES `clinic`.`doctors` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_appointment_user`
    FOREIGN KEY (`id_user`)
    REFERENCES `clinic`.`users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `clinic`.`contacts`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `clinic`.`contacts` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `subject` VARCHAR(45) NOT NULL,
  `message` VARCHAR(1000) NOT NULL,
  `id_user` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_contact_user_idx` (`id_user` ASC),
  CONSTRAINT `fk_contact_user`
    FOREIGN KEY (`id_user`)
    REFERENCES `clinic`.`users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `clinic`.`exams`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `clinic`.`exams` (
  `id` CHAR(10) NOT NULL,
  `url_exam` VARCHAR(45) NOT NULL,
  `id_user` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `code_UNIQUE` (`id` ASC),
  INDEX `id_user_idx` (`id_user` ASC),
  CONSTRAINT `fk_exam_user`
    FOREIGN KEY (`id_user`)
    REFERENCES `clinic`.`users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `clinic`.`schedules`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `clinic`.`schedules` (
  `id` INT NOT NULL,
  `day_of_week` CHAR(3) NOT NULL,
  `start_time` TIME NOT NULL,
  `end_time` TIME NOT NULL,
  `id_doctor` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_schedule_doctor_idx` (`id_doctor` ASC),
  CONSTRAINT `fk_schedule_doctor`
    FOREIGN KEY (`id_doctor`)
    REFERENCES `clinic`.`doctors` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- SET SQL_MODE=@OLD_SQL_MODE;
-- SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
-- SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- INSERTS
insert into clinic.departments (id, name, description, url_photo) values
(1, 'Cardiology', 'Cardiology is dedicated to the diagnosis and treatment of heart disease.', 'images/departments/1.jpg'),
(2, 'Dentistry', 'Dentistry is dedicated to the prevention, diagnosis and treatment of diseases of the teeth and their supporting structures.', 'images/departments/2.jpg'),
(3, 'Dermatology', 'Dermatology is dedicated to the prevention, diagnosis and medical and surgical treatment of diseases of the skin and mucous membranes.', 'images/departments/3.jpg'),
(4, 'Nutrition', 'Nutrition conducts nutritional evaluations and provides tailored meal plans for a variety of patients.', 'images/departments/4.jpg'),
(5, 'Ophthalmology', 'Ophthalmology is dedicated to diagnosing and treating eye diseases.', 'images/departments/5.jpg'),
(6, 'Urology', 'Urology is dedicated to the diagnosis and medical and surgical treatment of diseases of the urinary tract and male genital tract.', 'images/departments/6.jpeg')

;

insert into clinic.doctors (id, first_name, last_name, description, url_photo, id_department) values
(1, 'Tomas', 'Hardi', 'Integer pede justo, lacinia eget, tincidunt eget, tempus vel, pede. Morbi porttitor lorem id ligula. Suspendisse ornare consequat lectus. In est risus, auctor sed, tristique in, tempus sit amet, sem. Fusce consequat.', 'images/doctors/1.jpg', 1),
(2, 'Glennie', 'Ewestace', 'Morbi non quam nec dui luctus rutrum. Nulla tellus. In sagittis dui vel nisl.', 'images/doctors/2.jpg', 1),
(3, 'Rik', 'Switzer', 'Curabitur convallis. Duis consequat dui nec nisi volutpat eleifend. Donec ut dolor.', 'images/doctors/3.jpg', 2),
(4, 'Mario', 'Ledgley', null, 'images/doctors/4.jpg', 2),
(5, 'Karola', 'Gannon', null, 'images/doctors/5.jpg', 5),
(6, 'Ivory', 'Gaymar', 'Nullam orci pede, venenatis non, sodales sed, tincidunt eu, felis. Fusce posuere felis sed lacus. Morbi sem mauris, laoreet ut, rhoncus aliquet, pulvinar sed, nisl. Nunc rhoncus dui vel sem.', 'images/doctors/6.jpg', 5),
(7, 'Grove', 'Friman', null, 'images/doctors/7.jpg', 4),
(8, 'Ardys', 'Snawdon', 'Nam nulla. Integer pede justo, lacinia eget, tincidunt eget, tempus vel, pede. Morbi porttitor lorem id ligula. Suspendisse ornare consequat lectus.', 'images/doctors/8.jpg', 1),
(9, 'Mendy', 'Delahunt', 'Nunc purus. Phasellus in felis. Donec semper sapien a libero. Nam dui.', 'images/doctors/9.jpg', 3),
(10, 'Jay', 'Moodycliffe', null, 'images/doctors/10.jpg', 6)
;

insert into clinic.schedules (id, day_of_week, start_time, end_time, id_doctor) values
(1,  'MON', '09:00:00', '12:00:00', 1),
(2,  'WED', '14:00:00', '17:00:00', 1),
(3,  'TUE', '10:00:00', '13:00:00', 2),
(4,  'TUE', '15:00:00', '17:00:00', 2),
(5,  'FRI', '14:00:00', '17:00:00', 2),
(6,  'TUE', '09:00:00', '12:00:00', 3),
(7,  'TUE', '14:00:00', '19:00:00', 3),
(8,  'WED', '09:00:00', '12:00:00', 4),
(9,  'THU', '09:00:00', '12:00:00', 4),
(10, 'THU', '14:00:00', '15:00:00', 4),
(11, 'SAT', '13:00:00', '15:00:00', 5),
(12, 'SUN', '09:00:00', '11:00:00', 5),
(13, 'MON', '11:00:00', '12:00:00', 6),
(14, 'MON', '14:00:00', '20:00:00', 6),
(15, 'WED', '14:00:00', '20:00:00', 6),
(16, 'TUE', '09:00:00', '11:00:00', 7),
(17, 'TUE', '13:00:00', '15:00:00', 7),
(18, 'FRI', '15:00:00', '19:00:00', 8),
(19, 'SAT', '09:00:00', '13:00:00', 8),
(20, 'MON', '12:00:00', '16:00:00', 9),
(21, 'THU', '16:00:00', '20:00:00', 9),
(22, 'SAT', '09:00:00', '11:00:00', 10),
(23, 'SUN', '09:00:00', '11:00:00', 10),
(24, 'SUN', '14:00:00', '17:00:00', 10)
;

insert into clinic.users (id, username, password, first_name, last_name, phone, email) values
(1, 'admin', SHA2('admin', 512), 'John', 'Lucas', '000000000', 'admin@ehealthcorp.com'),
(2, 'drake98', SHA2('drake1', 512), 'Drake', 'Joshua', '911321432', 'drake.joshua@hotmail.com'),
(3, 'janine77', SHA2('ilikeroses', 512), 'Janine', 'Ryanne', '913123456', 'janine.ry@gmail.com'),
(4, 'sussybaka', SHA2('wethebestmusic', 512), 'Susan', 'Reynolds', '918375832', 'susanolds@gmail.com'),
(5, 'hectorian', SHA2('im2good4you', 512), 'Hector', 'Frederic', '931883029', 'h.fred@hotmail.com')
;

insert into clinic.exams (id, url_exam, id_user) values
('0000000000', '0000000000.pdf', null),
('1111111111', '1111111111.pdf', null),
('2222222222', '2222222222.pdf', 2),
('3333333333', '3333333333.pdf', 3),
('4444444444', '4444444444.pdf', 4),
('5555555555', '5555555555.pdf', 5)
;

insert into clinic.contacts (id, subject, message, id_user) values
(1, 'Want to know your street address', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.', 2),
(2, 'I have a dream', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Magnis dis parturient montes nascetur ridiculus mus mauris. Nisi scelerisque eu ultrices vitae auctor eu augue. Pretium viverra suspendisse potenti nullam ac tortor vitae purus faucibus. Aliquam ut porttitor leo a diam sollicitudin tempor id. Sit amet nisl purus in. Proin fermentum leo vel orci porta non. Nunc non blandit massa enim nec dui. Neque gravida in fermentum et. Dolor magna eget est lorem ipsum dolor sit amet. Dictum sit amet justo donec. Viverra maecenas accumsan lacus vel facilisis volutpat. Ut tristique et egestas quis ipsum suspendisse ultrices gravida.', 3),
(3, 'Google gave me a bad diagnosis', 'Dui nunc mattis enim ut tellus elementum sagittis. Lacus laoreet non curabitur gravida arcu ac tortor. Nibh praesent tristique magna sit amet purus. Nunc congue nisi vitae suscipit tellus mauris a diam. Elementum nibh tellus molestie nunc non blandit. Turpis tincidunt id aliquet risus feugiat in ante. Faucibus purus in massa tempor nec feugiat nisl pretium fusce. Tortor consequat id porta nibh venenatis cras. Ultrices dui sapien eget mi proin sed. Id leo in vitae turpis massa sed.', 4)
;

insert into clinic.appointments (id, message, start_date, end_date, id_doctor, id_user) values
(1, 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Tempor nec feugiat nisl pretium fusce. Nibh tellus molestie nunc non blandit massa enim nec dui. Mauris a diam maecenas sed enim. Pharetra massa massa ultricies mi quis hendrerit dolor magna. Vitae turpis massa sed elementum tempus egestas sed sed risus. Nibh tortor id aliquet lectus proin nibh nisl condimentum. Ornare quam viverra orci sagittis eu. Et odio pellentesque diam volutpat commodo sed egestas egestas fringilla. Accumsan sit amet nulla facilisi morbi tempus iaculis. Eget duis at tellus at urna condimentum mattis pellentesque id. Nibh praesent tristique magna sit amet. Eu augue ut lectus arcu.', '2022-11-07 09:00:00', '2022-11-07 10:00:00', 1, 2),
(2, 'Risus nullam eget felis eget. Tempus egestas sed sed risus pretium quam. Sagittis vitae et leo duis ut diam quam nulla. Tincidunt nunc pulvinar sapien et ligula ullamcorper malesuada proin. Pellentesque habitant morbi tristique senectus et netus et malesuada fames. Morbi tristique senectus et netus et malesuada fames ac turpis. Faucibus ornare suspendisse sed nisi lacus sed viverra tellus in. Sed turpis tincidunt id aliquet risus feugiat. Quam vulputate dignissim suspendisse in est ante in. Dignissim enim sit amet venenatis. Congue mauris rhoncus aenean vel. Est sit amet facilisis magna etiam tempor. Scelerisque fermentum dui faucibus in. Senectus et netus et malesuada fames ac turpis egestas sed. Eget aliquet nibh praesent tristique magna sit amet purus. Sed libero enim sed faucibus turpis in. Dignissim suspendisse in est ante in nibh mauris cursus. Porttitor massa id neque aliquam vestibulum.', '2022-11-08 11:00:00', '2022-11-08 12:00:00', 2, 3),
(3, 'Placerat orci nulla pellentesque dignissim enim sit amet venenatis. Auctor augue mauris augue neque. Quam pellentesque nec nam aliquam sem et. Tristique risus nec feugiat in fermentum posuere urna nec tincidunt. Elementum sagittis vitae et leo duis. Ac auctor augue mauris augue neque gravida in fermentum. Eu turpis egestas pretium aenean. Sed id semper risus in. Aliquet bibendum enim facilisis gravida. Id porta nibh venenatis cras sed felis. Ac orci phasellus egestas tellus. Elementum curabitur vitae nunc sed velit dignissim sodales. Sit amet risus nullam eget felis eget nunc. Eros donec ac odio tempor orci. Congue mauris rhoncus aenean vel. Maecenas volutpat blandit aliquam etiam erat velit scelerisque in.', '2022-11-08 12:00:00', '2022-11-08 13:00:00', 2, 4),
(4, 'Blandit massa enim nec dui. Massa tincidunt dui ut ornare lectus sit. Aliquet lectus proin nibh nisl condimentum id venenatis. Enim blandit volutpat maecenas volutpat blandit aliquam. Pretium nibh ipsum consequat nisl vel. Eget dolor morbi non arcu risus quis varius quam. Ut enim blandit volutpat maecenas. Bibendum enim facilisis gravida neque convallis a cras semper. Aliquam nulla facilisi cras fermentum. Nunc aliquet bibendum enim facilisis gravida. Felis donec et odio pellentesque diam volutpat commodo sed. Ut eu sem integer vitae justo eget. Egestas quis ipsum suspendisse ultrices gravida dictum fusce ut. Suspendisse sed nisi lacus sed viverra tellus in hac. Facilisis gravida neque convallis a cras semper auctor.', '2022-11-09 09:00:00', '2022-11-09 10:00:00', 4, 5)
;
