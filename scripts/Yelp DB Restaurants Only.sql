/**** REDUCE DATASET TO RESTAURANT INFO ONLY *****/

/* Note, if you lose connection to MySQL Server after 30 seconds, you can extend the wait time via Edit > Preferences > SQL Editor > (MySQL Session >) DBMS Connection Read Timeout */

/* Restaurants make up about 1/3 of Yelp's businesses */
SELECT COUNT(*) FROM category WHERE category = 'Restaurants';    /* 51,613 */

/*    Table Row Counts:                 BEFORE        AFTER     */
SELECT COUNT(*) FROM attribute;    /*  1,229,805       863,108  */
SELECT COUNT(*) FROM business;     /*    156,639        51,613  */
SELECT COUNT(*) FROM category;     /*    590,290       196,281  */
SELECT COUNT(*) FROM checkin;      /*  3,738,750     1,792,268  */
SELECT COUNT(*) FROM elite_years;  /*    180,563       166,705  */
SELECT COUNT(*) FROM friend;       /* 39,846,890    39,495,790  */
SELECT COUNT(*) FROM hours;        /*     ??           251,310  */
SELECT COUNT(*) FROM photo;        /*    196,278       189,253  */
SELECT COUNT(*) FROM review;       /*  4,736,897     2,927,731  */
SELECT COUNT(*) FROM tip;          /*  1,028,802       657,605  */
SELECT COUNT(*) FROM user;         /*  1,183,362     1,183,362  */
                                   /*   11.0 GB         8.6 GB  */

SET SQL_SAFE_UPDATES = 0;
/* Also had to remove Select max records restriction in Edit > Preferences > SQL Editor > SQL Execution > Uncheck 'Limit Rows' */   

DELETE FROM attribute WHERE business_id NOT IN (SELECT business_id FROM category WHERE category = 'Restaurants'); 
DELETE FROM checkin WHERE business_id NOT IN (SELECT business_id FROM category WHERE category = 'Restaurants'); 
DELETE FROM hours WHERE business_id NOT IN (SELECT business_id FROM category WHERE category = 'Restaurants'); 
DELETE FROM photo WHERE business_id NOT IN (SELECT business_id FROM category WHERE category = 'Restaurants'); 
DELETE FROM review WHERE business_id NOT IN (SELECT business_id FROM category WHERE category = 'Restaurants'); 
DELETE FROM tip WHERE business_id NOT IN (SELECT business_id FROM category WHERE category = 'Restaurants'); 

/* Tricky to delete category rows because you can't update a table that's part of the subquery */
DROP TABLE IF EXISTS not_restaurants; 
CREATE TEMPORARY TABLE not_restaurants (id VARCHAR(22) NOT NULL, PRIMARY KEY(id));     /* Indexed to speed up search during deletion */
INSERT INTO not_restaurants SELECT id FROM business WHERE id NOT IN (SELECT business_id FROM category WHERE category = 'Restaurants'); 
SELECT COUNT(*) FROM not_restaurants;   /* 105,026 */ 
DELETE FROM category WHERE business_id IN (SELECT id FROM not_restaurants);  /* Delete rate = 26 records/sec (no index) -> 5000 records/sec (with index) */

/* Have to perform deletion from Business table last because other tables have foreign key constraints on Business.id */
DELETE FROM business WHERE id IN (SELECT id FROM not_restaurants);        


/* On the theory that friends are useless to us if they have not reviewed or provided a tip about a restaurant, all such persons are deleted */
DROP TABLE IF EXISTS norest_reviewers;
CREATE TEMPORARY TABLE norest_reviewers (id VARCHAR(22) NOT NULL, INDEX(id));     /* Indexed to speed up search during deletion */
/*Note: User has duplicate entry '-Ag1PS0_G0yGxLWv_pULiA' for primary key; This really screws things up */ 
INSERT INTO norest_reviewers SELECT id FROM user;                              /* List of all users = 1,183,362 */
DELETE FROM norest_reviewers WHERE id IN (SELECT user_id FROM review);         /* Remove those who reviewed a restaurant - 823,317 removed*/
DELETE FROM norest_reviewers WHERE id IN (SELECT user_id FROM tip);            /* Remove those who provided a restaurant tip - 18,086 removed */
SELECT COUNT(*) FROM norest_reviewers;                                         /* 341,959 haven't reviewed or provided a tip (29% of users)*/

DELETE FROM elite_years WHERE user_id IN (SELECT id FROM norest_reviewers);


/* FOLLOWING WERE NOT COMPLETED */
DELETE FROM friend WHERE user_id IN (SELECT id FROM norest_reviewers) LIMIT 100000;       /* Delete either side of friendship when person is a non-reviewer */
DELETE FROM friend WHERE friend_id IN (SELECT id FROM norest_reviewers) LIMIT 100000;    /* INCOMPLETE - 39M rows is taking way too long */ 
  
/* Have to delete from User table last because other tables have foreign key constraints on User.id   */ 
DELETE FROM user WHERE id IN (SELECT id FROM norest_reviewers);                /* Can't clean this until Friend table is clean, but Friend is too big to operate on */

/* Use following when connection dropped and table still locked */ 
SHOW PROCESSLIST;
KILL 10928;