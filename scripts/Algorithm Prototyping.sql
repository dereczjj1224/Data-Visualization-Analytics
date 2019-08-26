/*** PROTOTYPING SIMILARITY ALGORITHMS ***/

/*** 1. YELP_PHOENIX TABLE SIZES FOR REFERENCE ***/
                                   /*    BEFORE         AFTER    */  
SELECT COUNT(*) FROM attribute;    /*  1,229,805        63,986   */
SELECT COUNT(*) FROM business;     /*    156,639         3,550   */
SELECT COUNT(*) FROM category;     /*    590,290        13,690   */
SELECT COUNT(*) FROM friend;       /* 39,846,890       553,304   */
SELECT COUNT(*) FROM review;       /*  4,736,897       303,952   */
SELECT COUNT(*) FROM user;         /*  1,183,362       112,333   */
                                   /*   11.0 GB        360 MB    */

/*** 2. STARTING POINTS ***/
/* Select a single restaurant */
SET @business = '8xrwjD-Udv7cm_emVcVo3A';                          /* Giovanni's Pizza & Pasta, Downtown Pitsburgh, PA */
SELECT @zip := postal_code FROM business WHERE id = @business;    /* Get zip code = 15222   */
SELECT category FROM category WHERE business_id = @business;     /* Pizza, Restaurants, Food Delivery Services, Food, Salad, Italian */
 
/* Select an "active user" who has reviewed this restaurant */
SELECT r.user_id, u.name FROM review AS r JOIN user AS u ON r.user_id = u.id WHERE business_id = @business;
SET @user = 'gfljrmMyT679L2ZKqbGajQ';           /* Patty - 3 reviews */
SET @user = 'Qp8SEXoDbYeRRTx2KAHOyQ';          /* Idiforu - 1 review */
SET @user = 'FXPzqAgnpbKDTUIT-fVs6g';         /* ben - 4 reviews */
SET @user = 'XYSDrIef7g4Gmp3lNFVO6A';        /* Neal- 88 reviews */
SET @user = 'jJk-w0Szkvs_H_D2KJnU3w';       /* Jon - 1 review */
SET @user = 'Ewywg-lLPxm_SaklKbElkw';      /* Nafeez - 5 reviews */
SET @user = 'PRmgrDZYBIt4J53s5ZBTDA';     /* Tim - 2 reviews */
SET @user = '_dhQV4M0zQcX--2Cxnbi8g';    /* Rick - 1 review */
SET @user = 'PR7XS6OA-6ylu8sLGObUsQ';   /* Chris - 19 reviews */
SET @user = 'moINbO61fGW-rB9XjyEltA';  /* Paul - 7 reviews */
SET @user = 'qK296Vai91sPZqKvUk8V9g'; /* Jordan - 1 review */

/*** 3. LIKE-MINDED USERS ***/
/* Restaurants reviewed by active user (and rating given) */
DROP TABLE IF EXISTS common_rests;
CREATE TEMPORARY TABLE IF NOT EXISTS common_rests AS (SELECT r.business_id, r.stars, r.user_id, u.name FROM review AS r JOIN user AS u ON r.user_id = u.id WHERE user_id = @user);
SELECT * FROM common_rests ORDER BY business_id; 

/* Other users who have reviewed these common restaurants */
DROP TABLE IF EXISTS like_diners;
CREATE TEMPORARY TABLE IF NOT EXISTS like_diners AS (SELECT r.business_id, r.stars, r.user_id, u.name FROM review AS r JOIN user AS u ON r.user_id = u.id WHERE r.business_id IN (SELECT business_id FROM common_rests));
SELECT * FROM like_diners ORDER BY business_id, stars;    /* For Neal's 88 reviews: 11.5 secs to find 15001 like diners */

/* Ordered by number of matching restaurants (Pointless if active user only has 1 review) */
SELECT COUNT(user_id) AS count, business_id, stars, user_id, name FROM like_diners GROUP BY user_id ORDER BY count DESC;

/* Others who have given same rating to these common restaurants */
DROP TABLE IF EXISTS like_minded;
CREATE TEMPORARY TABLE IF NOT EXISTS like_minded AS (SELECT ld.business_id, ld.stars, ld.user_id, ld.name FROM like_diners AS ld JOIN common_rests AS cr ON (ld.business_id = cr.business_id AND ld.stars=cr.stars)); /* 68 rating-matched users */  
SELECT * FROM like_minded ORDER BY business_id;  
 
/* Ordered by number of same-rated matching restaurants */
SELECT COUNT(user_id) AS count, business_id, stars, user_id, name FROM like_minded GROUP BY user_id ORDER BY count DESC;
    
    
/* CONCLUSIONS: 
/* Even if an active user has given few reviews, easy to find many other users reviewing the same restaurants
/* Among those users, there may be several with the identical rating (no complicated similarity calculations required!) 
/* However, unless active user has many reviews, probably few other users will have dined at multiple same restaurants
/* Even fewer, if any, dining at multiple same restaurants when require to have same rating */
/* Net, for active users with few reviews, strength of user similarity as basis for recommendations is questionable -> Switch to "item-based" restaurant comparisons?        
 
/* Curse of big data is that similarity calculations don't scale
/* OTOH, with lots of user/restaurant/rating overlap, the similarity calcs don't have to be as precise to discern the Top-N
/* We could test how well "quick and dirty" calcs yield the same like-minded rankings 
 
 
 
 /*** LIKE-ATTENDED RESTAURANTS ***/
SET @business = '8xrwjD-Udv7cm_emVcVo3A';       /* Giovanni's Pizza & Pasta - 126 reviewers */
SET @business = 'NvHGOIIukJ4y3iFswY-k8g';      /* Broadway Brunch - 26 reviewers */
SET @business = 'ZJdOOIubTizd1eqECkeK-Q';     /* Gran Agave Mexican Restaurant - 123 reviewers */
SELECT name FROM business WHERE id = @business;

/* Users who reviewed this active restaurant (and rating given) */
DROP TABLE IF EXISTS common_custs;
CREATE TEMPORARY TABLE IF NOT EXISTS common_custs AS (SELECT r.user_id, r.stars, r.business_id, b.name FROM review AS r JOIN business AS b ON r.business_id = b.id WHERE business_id = @business);
SELECT * FROM common_custs ORDER BY user_id; 

/* Other restaurants who have been reviewed by these common users */
DROP TABLE IF EXISTS like_attended;
CREATE TEMPORARY TABLE IF NOT EXISTS like_attended AS (SELECT r.user_id, r.stars, r.business_id, b.name FROM review AS r JOIN business AS b ON r.business_id = b.id WHERE r.user_id IN (SELECT user_id FROM common_custs));
SELECT * FROM like_attended ORDER BY user_id, stars;    

/* Ordered by number of matching customers - This looks promising! - Could also filter on common category names */
SELECT COUNT(business_id) AS count, user_id, stars, business_id, name FROM like_attended GROUP BY business_id ORDER BY count DESC;

/* Restaurants who have been given same rating by these common users - This is less useful */
DROP TABLE IF EXISTS like_rated;
CREATE TEMPORARY TABLE IF NOT EXISTS like_rated AS (SELECT la.user_id, la.stars, la.business_id, la.name FROM like_attended AS la JOIN common_custs AS cc ON (la.user_id = cc.user_id AND la.stars=cc.stars));   
SELECT * FROM like_rated ORDER BY user_id;  
 
/* Ordered by number of common customers providing the same-rating */
SELECT COUNT(user_id) AS count, business_id, stars, user_id, name FROM like_minded GROUP BY user_id ORDER BY count DESC;
    