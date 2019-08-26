/**** REDUCE DATASET TO PHOENIX INFO ONLY *****/

/* This reduction performed after SQL Script: Yelp DB Restaurant Only */

/* Note, if you lose connection to MySQL Server after 30 seconds, you can extend the wait time via Edit > Preferences > SQL Editor > (MySQL Session >) DBMS Connection Read Timeout */


/*    Table Row Counts:           BEFORE REST REDUX  AFTER REST REDUX     AFTER PHOENIX REDUX */
SELECT COUNT(*) FROM attribute;    /*  1,229,805       863,108                63,986       */
SELECT COUNT(*) FROM business;     /*    156,639        51,613                 3,550       */
SELECT COUNT(*) FROM category;     /*    590,290       196,281                13,690       */
SELECT COUNT(*) FROM checkin;      /*  3,738,750     1,792,268             Table Deleted   */
SELECT COUNT(*) FROM elite_years;  /*    180,563       166,705             Table Deleted   */
SELECT COUNT(*) FROM friend;       /* 39,846,890    39,495,790               553,304       */
SELECT COUNT(*) FROM hours;        /*     ??           251,310             Table Deleted   */
SELECT COUNT(*) FROM photo;        /*    196,278       189,253             Table Deleted   */
SELECT COUNT(*) FROM review;       /*  4,736,897     2,927,731               303,952       */
SELECT COUNT(*) FROM tip;          /*  1,028,802       657,605             Table Deleted   */
SELECT COUNT(*) FROM user;         /*  1,183,362     1,183,362               112,333       */
                                   /*   11.0 GB        8.6 GB                 360 MB       */

SET SQL_SAFE_UPDATES = 0;
/* Also had to remove Select max records restriction in Edit > Preferences > SQL Editor > SQL Execution > Uncheck 'Limit Rows' */   

/* CLEAN UP BUSINESS LISTINGS TO CORRECT PHOENIX MISSPELLINGS AND OTHER PROBLEMS */
/* Start with Zip Codes in Phoenix area: Codes range from 85001 - 85087, with some 852XX and 853xx */
SELECT postal_code FROM business WHERE city='Phoenix' GROUP BY postal_code;
/* Using the 85001 - 85087 zip codes, we see several misspellings of Phoenix: Pheonix, Pheonix AZ, 'Phoenix Valley', 'Phx'
/* We also see several census-designated areas and "urban villages" that are actually within the Phoenix metropolitan area: Ahwatukee, Anthem, Central City/Central City Village, South Mountain 
/* FYI, these share Phoenix zip codes but are legitimately separate cities: Chandler, Glendale, Mesa, Paradise Valley
/* Correct misspellings and city names that are in the Phoenix Metropolitan area */ 
UPDATE business SET city = 'Phoenix' WHERE city = 'Pheonix';            /* 4 rows changed */
UPDATE business SET city = 'Phoenix' WHERE city = 'Pheonix AZ';        /* 1 row changed */
UPDATE business SET city = 'Phoenix' WHERE city = 'Phoenix Valley';   /* 1 row changed */
UPDATE business SET city = 'Phoenix' WHERE city = 'Phx';             /* 1 row changed */
UPDATE business SET city = 'Phoenix' WHERE city = 'Ahwatukee' AND postal_code > 85000 AND postal_code < 85087;               /* 16 rows changed */
UPDATE business SET city = 'Phoenix' WHERE city = 'Anthem' AND postal_code > 85000 AND postal_code < 85087;                 /* 90 rows changed */
UPDATE business SET city = 'Phoenix' WHERE city = 'Central City' AND postal_code > 85000 AND postal_code < 85087;          /* 1 row changed */
UPDATE business SET city = 'Phoenix' WHERE city = 'Central City Village' AND postal_code > 85000 AND postal_code < 85087; /* 1 row changed */
UPDATE business SET city = 'Phoenix' WHERE city = 'South Mountain' AND postal_code > 85000 AND postal_code < 85087;      /* 1 row changed */

/* Delete restaurants outside of Phoenix from the ATTRIBUTE and CATEGORY tables */
DROP TABLE IF EXISTS phx_restaurants; 
CREATE TEMPORARY TABLE phx_restaurants (id VARCHAR(22) NOT NULL, PRIMARY KEY(id));     /* Indexed to speed up search during deletion */
INSERT INTO phx_restaurants SELECT id FROM business WHERE city = 'Phoenix'; 
SELECT COUNT(*) FROM phx_restaurants;   /* 3,550 Phoenix restaurants */ 

DELETE FROM attribute WHERE business_id NOT IN (SELECT id FROM phx_restaurants); 
DELETE FROM category WHERE business_id NOT IN (SELECT id FROM phx_restaurants);
/*DELETE FROM review WHERE business_id NOT IN (SELECT id FROM phx_restaurants);     /* This one crashed - lock table overflow */

/* REVIEW and Friend tables are way too big to delete from; Instead, we need to pull out the data we need into new tables */ 
/* Make copy of Review table with just the reviews of Phoenix restaurants */
CREATE TABLE phx_review (SELECT * FROM review WHERE business_id IN (SELECT id FROM phx_restaurants));   /* This one crashed too */

/* How about we break the task down into digestible pieces? */
DROP TABLE IF EXISTS splitable_restaurants; 
CREATE TEMPORARY TABLE splitable_restaurants (split INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY, id VARCHAR(22) NOT NULL);     /* We'll split the table on split value */
INSERT INTO splitable_restaurants (id) SELECT id FROM business WHERE city = 'Phoenix'; 
SELECT COUNT(*) FROM splitable_restaurants;   /* 3,550 Phoenix restaurants */ 
SELECT * FROM splitable_restaurants LIMIT 10;

/* Create empty table with schema of Review */
CREATE TABLE phx_review (SELECT * FROM review WHERE 0=1);
ALTER TABLE phx_review ADD PRIMARY KEY(id);
ALTER TABLE phx_review ADD CONSTRAINT fk_review_biz FOREIGN KEY (business_id) REFERENCES business(id);
ALTER TABLE phx_review ADD CONSTRAINT fk_review_uzer FOREIGN KEY (user_id) REFERENCES user(id);

/* Build out the Phoenix reviews table, 500 business id's at a time (900 failed) */
INSERT INTO phx_review SELECT * FROM review WHERE business_id IN (SELECT id FROM splitable_restaurants WHERE split BETWEEN 1 AND 500);  
INSERT INTO phx_review SELECT * FROM review WHERE business_id IN (SELECT id FROM splitable_restaurants WHERE split BETWEEN 501 AND 1000);  
INSERT INTO phx_review SELECT * FROM review WHERE business_id IN (SELECT id FROM splitable_restaurants WHERE split BETWEEN 1001 AND 1500);
INSERT INTO phx_review SELECT * FROM review WHERE business_id IN (SELECT id FROM splitable_restaurants WHERE split BETWEEN 1501 AND 2000);
INSERT INTO phx_review SELECT * FROM review WHERE business_id IN (SELECT id FROM splitable_restaurants WHERE split BETWEEN 2001 AND 2500);
INSERT INTO phx_review SELECT * FROM review WHERE business_id IN (SELECT id FROM splitable_restaurants WHERE split BETWEEN 2501 AND 3000);
INSERT INTO phx_review SELECT * FROM review WHERE business_id IN (SELECT id FROM splitable_restaurants WHERE split BETWEEN 3001 AND 3600);
SELECT COUNT(*) FROM phx_review;   /* 303,952 reviews of Phoenix restaurants */ 

/* Now that all non-Phoenix foreign key dependencies on business table have been removed, we'll be taking care of BUSINESS! */ 
DELETE FROM business WHERE city != 'Phoenix' LIMIT 10000; 
SELECT COUNT(*) FROM business;   /* 3,550 Phoenix restaurants */ 

/* Create empty table with schema of FRIEND */
CREATE TABLE phx_friend (SELECT * FROM friend WHERE 0=1);
/*ALTER TABLE phx_friend ADD INDEX user_id (user_id);            /* Note: InnoDB automatically indexes foreign keys, so this is an undesirable duplication */
ALTER TABLE phx_friend ADD CONSTRAINT fk_friend_uzer FOREIGN KEY (user_id) REFERENCES user(id);


/* Identify all users who have reviewed at least one Phoenix restaurant */
DROP TABLE IF EXISTS phx_reviewers; 
CREATE TEMPORARY TABLE phx_reviewers (split INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY, id VARCHAR(22) NOT NULL); 
INSERT INTO phx_reviewers (ID) SELECT user_id FROM phx_review GROUP BY user_id; 
SELECT COUNT(*) FROM phx_reviewers;   /* 112,333 distinct reviewers of Phoenix restaurants */ 
SELECT * FROM phx_reviewers LIMIT 10;

/* How about we add an index to Friend.user_id to speed things up? NOT necessary because InnoDB automatically indexes the foreign key */
ALTER TABLE friend ADD INDEX user_id (user_id);
SHOW INDEX FROM friend;

/* Build out the Phx_friend table, 20,000 user id's at a time */
/* We could make table smaller by also restricting friend_id to be a Phoenix reviewer, but this adds compute time and isn't necessary since friend_id isn't a foreign key */
INSERT INTO phx_friend SELECT * FROM friend WHERE user_id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 1 AND 20000);      /* About 90 seconds each */
INSERT INTO phx_friend SELECT * FROM friend WHERE user_id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 20001 AND 40000);  
INSERT INTO phx_friend SELECT * FROM friend WHERE user_id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 40001 AND 60000); 
INSERT INTO phx_friend SELECT * FROM friend WHERE user_id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 60001 AND 80000); 
INSERT INTO phx_friend SELECT * FROM friend WHERE user_id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 80001 AND 100000); 
INSERT INTO phx_friend SELECT * FROM friend WHERE user_id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 100001 AND 120000); 
SELECT COUNT(*) FROM phx_friend;     /* 4,944,154 Phoenix reviewers and all of their friends */

/* Now we should be able to go back and delete any non-Phoenix friends? 100K at a time? */
DELETE FROM phx_friend WHERE friend_id NOT IN (SELECT id FROM phx_reviewers) LIMIT 100000;  /* NO! Deletions are just a bad idea in general */

/* OK, let's copy over just the phoenix reviewer records where their friend is also a Phoenix reviewer */
CREATE TABLE friend (SELECT * FROM phx_friend WHERE 0=1);
ALTER TABLE friend ADD CONSTRAINT fk_friend_user FOREIGN KEY (user_id) REFERENCES user(id);

/* First we need to add an index to phx_friend.friend_id to speed the selection */
ALTER TABLE phx_friend ADD INDEX friend_id (friend_id);

INSERT INTO friend SELECT * FROM phx_friend WHERE friend_id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 1 AND 20000);  
INSERT INTO friend SELECT * FROM phx_friend WHERE friend_id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 20001 AND 40000);
INSERT INTO friend SELECT * FROM phx_friend WHERE friend_id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 40001 AND 60000);
INSERT INTO friend SELECT * FROM phx_friend WHERE friend_id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 60001 AND 80000);
INSERT INTO friend SELECT * FROM phx_friend WHERE friend_id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 80001 AND 100000);
INSERT INTO friend SELECT * FROM phx_friend WHERE friend_id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 100001 AND 120000);

SELECT COUNT(*) FROM friend;     /* 553,304 Phoenix reviewers and their phoenix-reviewer friends */

/* Let's repeat everything one more time for the USER table */
/* We have to delete from User table last because other tables have foreign key constraints on User.id   */ 
CREATE TABLE phx_user (SELECT * FROM user WHERE 0=1);
ALTER TABLE phx_user ADD PRIMARY KEY(id);

INSERT INTO phx_user SELECT * FROM user WHERE id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 1 AND 20000);  
INSERT INTO phx_user SELECT * FROM user WHERE id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 20001 AND 70000); 
INSERT INTO phx_user SELECT * FROM user WHERE id IN (SELECT id FROM phx_reviewers WHERE split BETWEEN 70001 AND 120000); 
SELECT COUNT(*) FROM phx_user;   /* 112,333 */
SELECT * FROM phx_user LIMIT 10; 

/* That wasn't too bad; Could we have just deleted from user? */
DELETE FROM user WHERE id NOT IN (SELECT id FROM phx_reviewers) LIMIT 30000;  /* No, deletions simply don't work */             

/* Use following when connection dropped and table still locked */ 
SHOW PROCESSLIST;
KILL 5;