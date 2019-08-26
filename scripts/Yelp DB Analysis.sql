/***** INITIAL STATISTICS *****/

/* Note, if you lose connection to MySQL Server after 30 seconds, you can extend the wait time via Edit > Preferences > SQL Editor > MySQL Session > Read DBMS Wait Timeout

/* 1 - Number of distinct users in DB = 1,183,362 */
SELECT COUNT(*) FROM user;  

/* 2 - Number of distinct businesses in DB = 156,639 */
SELECT COUNT(*) FROM business;  

/* 3 - Number of distinct reviews in DB = 3,717,133 */
/* (Query requires more than 5 minutes - Number of rows obtained from MYSQL Workbench Table Analyzer) */

/* On inspection of data, category = 'Restaurants' is the primary identifer of restaurants */
/* 4 - Number of distinct businesses with category='Restaurants' = 51,613 */
SELECT COUNT(*) FROM category WHERE category = 'Restaurants';

/* 5 - The category label 'Food' (without 'Restaurants' appears on many establishments such as Bakeries, Coffee & Tea, Juice stands, Pharmacy, etc. These can be excluded. */  
SELECT business_id, category FROM category WHERE business_id IN (SELECT business_id FROM category WHERE category = 'Food') AND business_id NOT IN (SELECT business_id FROM category WHERE category = 'Restaurants');

/* 6 - 'Food' also appears on 381 establishments labeled as Bars, Pubs, Lounges, and Nightlife. We may want to inculude these category labels, but only when combined with Food */
SELECT business_id, category FROM category WHERE business_id IN (SELECT business_id FROM category WHERE category = 'Food') AND business_id IN (SELECT business_id FROM category WHERE category = 'Bars' OR category = 'Pubs' OR category = 'Lounges' OR category = 'Nightlife') AND business_id NOT IN (SELECT business_id FROM category WHERE category = 'Restaurants') GROUP BY business_id;

/* 7 - A business may have multiple categories assigned to it. The maximum occurrence of categories for a restaurant in this DB is 24 */
SELECT COUNT(category) AS cats FROM category WHERE business_id IN (SELECT business_id FROM category WHERE category = 'Restaurants') GROUP BY business_id ORDER BY cats DESC;

/* 8 - The 51,613 restaurants share 196,281 categories, so each restaurant carries 3.8 categories on average */
SELECT COUNT(*) FROM category WHERE business_id IN (SELECT business_id FROM category WHERE category = 'Restaurants');

/* 9 - A business may have multiple reviews. The maximum number of reviews for a restaurant in this DB is 6978. */ 
SELECT COUNT(user_id) AS revs FROM review WHERE business_id IN (SELECT business_id FROM category WHERE category = 'Restaurants') GROUP BY business_id ORDER BY revs DESC;

/* 10 - The 51,613 restaurants share xxx reviews, so each restaurant has xx reviews on average */
/*SELECT COUNT(*) FROM review WHERE business_id IN (SELECT business_id FROM category WHERE category = 'Restaurants');   /* Don't run - Timeout at 5 minutes */

/* 11 - Unique cities represented in dataset (706 cities counting duplicates, eg Bedford Heights/Bedford Hts, Bellevue/Bellvue */
SELECT city, postal_code FROM business GROUP BY city, postal_code;
/* SELECT city, postal_code FROM business GROUP BY city, postal_code;   /* 10199 Unique City/Zip Code pairs */
 
/***** BUSINESS ALGORITHM 3A - PART 1: FIND PRIMARY COMPETITORS OF A BUSINESS BY SHARED ATTRIBUTES *****/
 
/* Note: Price category not provided in this dataset! */

/* Choose a business and get its zip code and category labels */
SET @business = '8xrwjD-Udv7cm_emVcVo3A';    
                      /* Giovanni's Pizza & Pasta, Downtown Pitsburgh, PA */
SELECT @zip := postal_code FROM business WHERE id = @business;    /* 15222   Only one value per variable */
SELECT category FROM category WHERE business_id = @business;     /* Pizza, Restaurants, Food Delivery Services, Food, Salad, Italian */

/* 108 competitors based on common zip code and at least one matching category (beyond restaurant) */
CREATE TEMPORARY TABLE IF NOT EXISTS comps AS (SELECT id, name, neighborhood, city, category FROM business AS b JOIN category AS c ON b.id = c.business_id 
    WHERE b.postal_code = @zip AND business_id IN (SELECT business_id FROM category WHERE category = 'Restaurants') 
    AND (c.category = 'Pizza' OR c.category = 'Food Delivery Services' OR c.category = 'Food' OR c.category = 'Salad' OR c.category = 'Italian') GROUP BY name);
SELECT * FROM comps;

/* For this exercise, we've matched on Pizza or Italian, as the most important categories - 53 competitors found */   
/* Further narrowing and ranking of competition possible by matching features in Attributes table */  
DROP TABLE comps;
CREATE TEMPORARY TABLE IF NOT EXISTS comps AS (SELECT id, name, neighborhood, city, category FROM business AS b JOIN category AS c ON b.id = c.business_id 
    WHERE b.postal_code = @zip AND business_id IN (SELECT business_id FROM category WHERE category = 'Restaurants') 
    AND (c.category = 'Pizza' OR /*c.category = 'Food Delivery Services' OR c.category = 'Food' OR c.category = 'Salad' OR */ c.category = 'Italian') GROUP BY name);
SELECT * FROM comps;  
  
  
/*****  BUSINESS ALGORITHM 3A - PART 2: FIND NEW PROSPECTS WHO HAVE REVIEWED THE COMPETITION BUT NOT OUR BUSINESS *****/  
  
/* 126 users who have already reviewed this business */
CREATE TEMPORARY TABLE IF NOT EXISTS my_reviewers AS (SELECT r.user_id, u.name FROM review AS r JOIN user AS u ON r.user_id = u.id WHERE business_id = @business);
SELECT * FROM my_reviewers; 
 
/* 3389 distinct users who have reviewed the 53 competitors */  
CREATE TEMPORARY TABLE IF NOT EXISTS their_reviewers AS (SELECT DISTINCT user_id FROM review WHERE business_id IN (SELECT id FROM comps)); 
SELECT * FROM their_reviewers;

/* Target the users who have not previously reviewed the original business */
SELECT tr.user_id, u.name FROM their_reviewers AS tr JOIN user AS u ON tr.user_id = u.id WHERE tr.user_id NOT IN (SELECT user_id FROM my_reviewers); 
 
 
 
/***** BUSINESS ALGORITHM 4 (3B): FIND THE THIRD ORDER NODES FROM A SELECTED BUSINESS *****/ 

/* 1st Order Nodes: 126 users who have already reviewed this business */
CREATE TEMPORARY TABLE IF NOT EXISTS my_reviewers AS (SELECT r.user_id, u.name FROM review AS r JOIN user AS u ON r.user_id = u.id WHERE business_id = @business);
SELECT * FROM my_reviewers; 

/* 2nd Order Nodes: The 2981 other restaurants my reviewers have also reviewed (run time 263 secs) */
SELECT DISTINCT business_id FROM review WHERE user_id IN (SELECT user_id FROM my_reviewers); 
/* This is exploding rapidly, so need to find a way to rank the nodes in order of importance */
/* The algorithm needs user visits as an indicator of interest level, but this is only available thru Yelp's WiFi program */

/* 2nd Order Nodes: Top 100 restaurants my reviewers have also reviewed */
DROP TABLE comps;
CREATE TEMPORARY TABLE IF NOT EXISTS comps AS (SELECT DISTINCT business_id FROM review WHERE user_id IN (SELECT user_id FROM my_reviewers) LIMIT 100);
SELECT * FROM comps; 

/* 3rd Order Nodes: 3389 distinct users who have reviewed the Top 100 other Restaurants (run time > 300 secs) */  
DROP TABLE their_reviewers;
CREATE TEMPORARY TABLE IF NOT EXISTS their_reviewers AS (SELECT DISTINCT user_id FROM review WHERE business_id IN (SELECT id FROM comps)); 
SELECT * FROM their_reviewers;


/***** CUSTOMER ALGORITHM 2 (BUSINESSS 4): FIND THE THIRD ORDER NODES FROM A SELECTED USER *****/ 

SELECT r.user_id, u.name FROM review AS r JOIN user AS u ON r.user_id = u.id WHERE business_id = '8xrwjD-Udv7cm_emVcVo3A';
SET @user = 'gfljrmMyT679L2ZKqbGajQ';

/* 1st Order Nodes: 3 businesses that this user has reviewed */
DROP TABLE my_businesses;
CREATE TEMPORARY TABLE IF NOT EXISTS my_businesses AS (SELECT business_id FROM review WHERE user_id = @user);
SELECT * FROM my_businesses; 

/* 2nd Order Nodes - 275 like-minded users who have reviewed the same businesses this user has */
CREATE TEMPORARY TABLE IF NOT EXISTS likeminded AS (SELECT user_id FROM review WHERE business_id IN (SELECT business_id FROM my_businesses));
SELECT * FROM likeminded;

/* 3rd Order Nodes: xxx distinct businesses reviewed by my like-minded users (run time > 300 secs)*/
CREATE TEMPORARY TABLE IF NOT EXISTS other_businesses AS (SELECT DISTINCT business_id FROM review WHERE user_id IN (SELECT user_id FROM likeminded));
SELECT ob.business_id, b.name FROM other_businesses AS ob JOIN business AS b ON ob.business_id = b.id;



/***** ALGORITHM 3 DATA FOR GEPHI CHART *****/

set @id1 = 'JTKzGJvIK9yuoUf-erV2qQ';
set @id2 = '4tJiL2mHKO-erM6xoZji9Q';
set @id3 = 'YjmbCvygeMj9dfJp6neQ_A';
set @id4 = 'JacuuWTDI4EU5-t7G6OIFw';
set @id5 = 'nMV7Sn15I87tDlHJiSE92A';
set @id6 = '1qYCUtw6_ehv7u_FxiE8IA';
set @id7 = 'YgO2v1VNtbPA7zgp0szJXA';
set @id8 = 'azE1DNVQFBU8boVbaJhj7w';
set @id9 = '7odNqxZDSR6ZVgxjp2r39A';
set @id10 = 'ZPAnqqAKLjg9uCN6Rk1lfg';
SELECT r.user_id, u.name FROM review AS r JOIN user AS u ON r.user_id = u.id WHERE r.business_id = @id10 LIMIT 10; 

/****** User named Polo who has reviewed Phoenix restaurants *****/
/* WARNING: 75 minute query */
/* dJCPmuMGFZoBJ9t89qnS0g  (2x)  */
/* CHa6N1KJtRmspb_-5RRjAA  (3x)  */
SELECT r.user_id FROM review AS r JOIN business AS b on r.business_id = b.id WHERE b.city = 'Phoenix' AND r.user_id IN(SELECT u.id FROM user AS u WHERE u.name = 'polo');

