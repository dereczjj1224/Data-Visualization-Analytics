# -*- coding: utf-8 -*-
#  *** These low-level modules are called by API routines ***

import logging

import math
import pandas as pd
# from sqlalchemy import select, and_, func

from bipolo import db

# Engine is the key to executing raw sql
engine = db.engine


# SEARCH MODE MODULES

# SEARCH returns matching restaurant names and business_ids
def search(string, limit):
    sql = """SELECT CONCAT(b.name, ' (', address, ')') AS name, id FROM business AS b 
             WHERE b.name LIKE '{xxx}' LIMIT {yyy}"""
    # Note: Double %% required since Python interprets single % for replacement
    sql = sql.format(xxx=string+'%%', yyy=limit)
    return pd.read_sql(sql, engine)


# FULL_LIST returns names and restaurant_ids for all Phoenix restaurants
# Frontend code will cache the list for local search handling
# Parms: NONE!

def full_list():
    sql = """SELECT CONCAT(name, ' (', address, ')') AS restaurant, id AS restaurant_id FROM business"""
    return pd.read_sql(sql, engine)


# EXPLORE AND ANALYSIS MODE MODULES

# Auxilary Functions to help us calculate user influence index
# Logdiv returns logn(val+1)/divisor up to a maximum value of 1
def inf(val, divisor):
    return min(math.log(val+1)/divisor, 1)

# Influence_calc considers # useful+funny+cool review votes, # friends, # total reviews, # fans, and average rating
def influence_calc (df):
    return round((inf(df['votes'],7) + inf(df['friends'],6) + inf(df['total_reviews'],6) + inf(df['fans'],5) + df['avg_rating']/5), 2)


# USER_PROFILE returns user details and influence index calculation
def user_profile(user_id):
    sql = """SELECT u.name, u.review_count AS total_reviews, u.average_stars AS avg_rating, u.yelping_since,  
         (u.useful + u.funny + u.cool) AS review_likes, u.fans, COUNT(f.user_id) AS friends  
         FROM user AS u LEFT JOIN friend AS f ON u.id = f.user_id WHERE u.id = '{xxx}'
         GROUP BY f.user_id"""
    sql = sql.format(xxx=user_id)
    active_user = pd.read_sql(sql, engine)

    # Calculate influence index subscores
    active_user['total_reviews_score'] = round(inf(active_user['total_reviews'], 6), 2)
    active_user['review_likes_score'] = round(inf(active_user['review_likes'], 7), 2)
    active_user['fans_score'] = round(inf(active_user['fans'], 5), 2)
    active_user['friends_score'] = round(inf(active_user['friends'], 6), 2)
    active_user['avg_rating_score'] = round(active_user['avg_rating'] / 5, 2)

    # Total subscores for final influence index
    active_user['influence'] = active_user['total_reviews_score'] + active_user['review_likes_score'] + \
                               active_user['fans_score'] + active_user['friends_score'] + active_user['avg_rating_score']
    active_user['influence'] = round(active_user['influence'], 2)

    return active_user


# RESTAURANT_PROFILE returns restaurant details with categories and attributes csv lists
def restaurant_profile(restaurant_id):
    # Get basic restaurant info
    sql = """SELECT b.name, b.id AS restaurant_id, b.stars AS avg_rating, b.review_count AS total_reviews, 
          b.neighborhood, b.address, b.city, b.state, b.postal_code AS zip 
          FROM business AS b WHERE b.id = '{xxx}'"""
    sql = sql.format(xxx=restaurant_id)
    active_restaurant = pd.read_sql(sql, engine)

    # Get category list as a csv string
    sql = """SELECT GROUP_CONCAT(category SEPARATOR ',') FROM category WHERE business_id = '{xxx}' GROUP BY business_id"""
    sql = sql.format(xxx=restaurant_id)
    categories = pd.read_sql(sql, engine)
    # Handle no info returned
    if (categories.empty):
        active_restaurant['categories'] = "(No category information)"
    else:
        active_restaurant['categories'] = categories.iloc[0, 0]

    # Get attribute list as a csv string
    sql = """SELECT GROUP_CONCAT(name SEPARATOR ',') FROM attribute WHERE business_id = '{xxx}' AND value = '1'"""
    sql = sql.format(xxx=restaurant_id)
    attributes = pd.read_sql(sql, engine)
    if (attributes.empty):
        active_restaurant['attributes'] = "(No attributes information)"
    else:
        active_restaurant['attributes'] = attributes.iloc[0, 0]

    return active_restaurant


# USER_RESTAURANT_RATING returns details of user-restaurant rating
def user_restaurant_rating(user_id, restaurant_id):
    # Query for review information of this user-restaurant pair
    sql = """SELECT b.name AS restaurant, b.id AS restaurant_id, u.name AS user, r.user_id AS user_id,
          r.stars AS rating, r.date, r.text AS review, r.useful, r.funny, r.cool 
          FROM review AS r JOIN business AS b ON r.business_id = b.id
          JOIN user AS u ON r.user_id = u.id
          WHERE r.user_id = '{xxx}' AND r.business_id = '{yyy}'"""
    sql = sql.format(xxx=user_id, yyy=restaurant_id)
    user_restaurant_rating = pd.read_sql(sql, engine)

    return user_restaurant_rating


# LIKE_USERS returns name and user_id information to build like user nodes (in graph and at bottom of screen).
# Also contains information to build similarity comparison bar graph of all like user nodes.
# Returns name and user_id information to build like user nodes at bottom of screen.
# Also contains information to build similarity comparison bar graph of all like user nodes.
def like_users(user_profile_df, selected_user_id, limit):
    # 1) Find second-order users (LMU's) who have reviewed the same restaurants as selected user
    # Notes:
    # - Performing subquery (vs. Group By) to get friend count so duplicate user_ids remain for rating similarity calculation
    # - Storing selected user's total review count for later use in review overlap calculation
    # - Storing selected user's restaurant ratings and computing max/min vs. each second order user
    # - Limiting first-order restaurants to 10 most popular (by average rating)
    # - Bizarre: MySQL doesn't support Limit in the sub-query, but it's OK in the sub-sub-query
    # - Limiting second-order like-minded user candidate to top 2000 with highest votes (a proxy for influence)
    sql = """SELECT b.name AS restaurant, b.id AS restaurant_id, r.stars, u.name AS user, r.user_id, 
          u.review_count AS total_reviews, (u.useful + u.funny + u.cool) AS votes, u.fans, u.average_stars AS avg_rating, 
         (SELECT COUNT(*) FROM friend AS f WHERE f.user_id = r.user_id) AS friends,
         (SELECT review_count FROM user WHERE id = '{xxx}') AS sel_reviews,
         (SELECT @sel := stars FROM review AS r2 WHERE r2.business_id = r.business_id AND r2.user_id = '{xxx}') AS sel_rating,
         GREATEST(r.stars, @sel) AS max, LEAST(r.stars, @sel) AS min
         FROM review AS r JOIN business AS b ON r.business_id = b.id 
         JOIN user AS u ON r.user_id = u.id 
         WHERE r.user_id != '{xxx}' AND b.id IN 
         (SELECT * FROM (SELECT business_id FROM review WHERE user_id = '{xxx}' ORDER BY stars LIMIT 10) AS x)
         ORDER BY votes DESC LIMIT 2000"""
    sql = sql.format(xxx=selected_user_id)
    like_users = pd.read_sql(sql, engine)
    # 2) Check length of like_users dataframe; If not enough, try adaptive algorithm???

    # 3) Calculate ratings similarity between selected user and each LMU
    # Count the number of restaurants reviewed by each user and separately sum the min and max ratings vs. selected user's ratings
    similarity = like_users.groupby('user_id') \
        .agg({'restaurant_id': 'size', 'max': 'sum', 'min': 'sum'}) \
        .rename(columns={'restaurant_id': 'shared_val', 'max': 'sum_max', 'min': 'sum_min'}) \
        .reset_index()

    # Jaccard similarity = Sum (min ratings) / Sum (max ratings)
    def sim(df):
        # return round(((float(df['sum_min'])/float(df['sum_max'])-0.2)*1.25),2)    # normalized to a 0-5 scale
        return round((float(df['sum_min']) / float(df['sum_max'])), 2)

    similarity['rate_sim_score'] = similarity.apply(sim, axis=1)

    # Record the summin / summax values used to calculate rate_sim_score
    def sim_val(df):
        return str(df['sum_min']) + ' / ' + str(df['sum_max'])

    similarity['rate_sim_val'] = similarity.apply(sim_val, axis=1)
    # Join ratings similarity on like user list (duplicating score on multiple user records)
    like_users = pd.merge(like_users, similarity.loc[:, ['user_id', 'shared_val', 'rate_sim_val', 'rate_sim_score']],
                          on='user_id')
    # Drop interim values that are no longer needed
    like_users = like_users.drop(['max', 'min'], axis=1)

    # 4) Calculate influence index using functions defined above for user_profile_df
    like_users['influence_val'] = like_users.apply(influence_calc, axis=1)
    like_users = like_users.drop(['stars', 'avg_rating', 'votes', 'fans', 'friends'], axis=1)

    # Record the influence score (simply influence value / 5)
    def influence_score(df):
        return round(df['influence_val'] / 5, 2)

    like_users['influence_score'] = like_users.apply(influence_score, axis=1)

    # 5) Calculate number of shared restaurant reviews
    # Review similarity = N/5 (this will help get more 1-2 order interconnectons)
    def shared(df):
        return round(min((float(df['shared_val']) / 5), 1), 2)

    like_users['shared_score'] = like_users.apply(shared, axis=1)

    # 6) Calculate restaurant overlap considering total reviews of both users
    # Create column for combined reviews of both users
    def combined(df):
        return str(df['shared_val']) + ' / ' + str(df['total_reviews'] + df['sel_reviews'])

    like_users['overlap_val'] = like_users.apply(combined, axis=1)

    # Review overlap = # shared / logn(combined review count)   but not greater than one
    def overlap(df):
        return round(min((df['shared_val'] / math.log(df['total_reviews'] + df['sel_reviews'])), 1), 2)

    like_users['overlap_score'] = like_users.apply(overlap, axis=1)
    like_users = like_users.drop(['total_reviews', 'sel_reviews'], axis=1)

    # 7) Calculate jaccard similarity of influence indices
    # Add selected user influence to dataframe, using user_profile_df passed in as parameter
    like_users['sel_influ'] = user_profile_df.iloc[0]['influence']

    # Influence similarity = min(influence)/max (influence)
    def influ_sim(df):
        return round(min(df['influence_val'], df['sel_influ']) / max(df['influence_val'], df['sel_influ']), 2)

    like_users['influ_sim_score'] = like_users.apply(influ_sim, axis=1)

    # Record the value used to calculate the influence similarity
    def influ_sim_val(df):
        return str(min(df['influence_val'], df['sel_influ'])) + ' / ' + str(max(df['influence_val'], df['sel_influ']))

    like_users['influ_sim_val'] = like_users.apply(influ_sim_val, axis=1)
    like_users = like_users.drop(['sel_influ'], axis=1)

    # 8) Calculate overall like-mindedness score
    # Like-mindedness = Reviewed restaurant overlap + Restaurant ratings similarity + # Shared reviews
    #     + User Influence Index + Influence Index similarity
    def final_score(df):
        return round((df['overlap_score'] + df['rate_sim_score'] + df['shared_score'] + df['influence_score'] + df[
            'influ_sim_score']), 2)

    like_users['lmu_score'] = like_users.apply(final_score, axis=1)

    # 9) Group by userid to clip at specified limit
    # Note: Taking max of LMU_score to get it into a dataframe
    limited = like_users.groupby('user_id').agg({'lmu_score': 'max'}).reset_index()
    limited.sort_values(['lmu_score'], ascending=False, inplace=True)
    # Note that Pandas does not reindex after sorting; If we don't reindex explictly, limit may choose unordered rows!!
    limited.reset_index(drop=True, inplace=True)
    # Join the lmu similarity score on the like users list (duplicating score on multiple restaurant records)
    # Inner join to remove users that are beyond the limit
    like_users = pd.merge(like_users, limited.loc[0:limit, ['user_id']], on='user_id', how='inner')

    # 10) Order columns by the Like Minded User Similarity table they will fill
    like_users = like_users[
        ['restaurant', 'restaurant_id', 'user', 'user_id', 'sel_rating', 'shared_val', 'shared_score', \
         'overlap_val', 'overlap_score', 'rate_sim_val', 'rate_sim_score', 'influence_val', \
         'influence_score', 'influ_sim_val', 'influ_sim_score', 'lmu_score']]

    # 11) Order by LMU similarity
    like_users.sort_values(['lmu_score', 'user_id'], ascending=False, inplace=True)
    like_users.reset_index(drop=True, inplace=True)

    return like_users


# LIKE_RESTAURANTS returns name and business_id info to build like restaurant nodes at bottom of screen.
# Also contains information to build similarity comparison bar graph of all like restaurant nodes
# Also returns information to compare similarity of two restaurant nodes
def like_restaurants(selected_restaurant_id, limit):
    # 1) Find second-order restaurants who have been reviewed by the same users, ordered by avg rating???
    # Notes:
    # - Storing selected restaurant's total review count for later use in review overlap calculation
    # - Storing selected restaurant's ratings and computing max/min vs. each second order competitor
    # - Limiting first-order reviewing users to 10 most useful
    # - Bizarre: MySQL doesn't support Limit in the sub-query, but it's OK in the sub-sub-query
    # - Limiting second-order competitive restaurants to top 1000 with highest usere rating
    sql = """SELECT u.name AS user, u.id AS user_id, r.stars AS user_rating, b.name AS restaurant, 
          r.business_id AS restaurant_id, b.postal_code AS zip, b.review_count AS reviews, b.stars AS avg_rating,
          (SELECT postal_code FROM business WHERE id = '{xxx}') AS sel_zip,          
          (SELECT review_count FROM business WHERE id = '{xxx}') AS sel_reviews,
          (SELECT @sel := stars FROM review AS r2 WHERE r2.user_id = r.user_id AND r2.business_id = '{xxx}') AS sel_rating,
          GREATEST(r.stars, @sel) AS max, LEAST(r.stars, @sel) AS min
          FROM review AS r JOIN business AS b ON r.business_id = b.id 
          JOIN user AS u ON r.user_id = u.id
          WHERE r.business_id != '{xxx}' AND u.id IN 
          (SELECT * FROM (SELECT user_id FROM review WHERE business_id = '{xxx}' ORDER BY useful LIMIT 10) AS x)
          ORDER BY r.stars DESC LIMIT 1000"""
    sql = sql.format(xxx=selected_restaurant_id)
    like_restaurants = pd.read_sql(sql, engine)

    # 2) Check length of like_restaurants dataframe; If not enough, try adaptive algorithm???

    # 3) Calculate ratings similarity between selected restaurant and each competitor
    # Count the number of users reviewing each restaurant and separately sum the min and max ratings vs. same user's review of selected restaurant    similarity = like_restaurants.groupby('user_id') \
    similarity = like_restaurants.groupby('restaurant_id') \
        .agg({'user_id': 'size', 'max': 'sum', 'min': 'sum'}) \
        .rename(columns={'user_id': 'shared_val', 'max': 'sum_max', 'min': 'sum_min'}) \
        .reset_index()

    # Jaccard similarity = Sum (min ratings) / Sum (max ratings)
    def sim(df):
        # return round(((float(df['sum_min'])/float(df['sum_max'])-0.2)*1.25),2)    # normalized to a 0-5 scale
        return round((float(df['sum_min']) / float(df['sum_max'])), 2)

    similarity['rate_sim_score'] = similarity.apply(sim, axis=1)

    # Record the summin / summax values used to calculate rate_sim_score
    def sim_val(df):
        return str(df['sum_min']) + ' / ' + str(df['sum_max'])

    similarity['rate_sim_val'] = similarity.apply(sim_val, axis=1)
    # Join ratings similarity on like restaurant list (duplicating score on multiple restaurant records)
    like_restaurants = pd.merge(like_restaurants, \
            similarity.loc[:, ['restaurant_id', 'shared_val', 'rate_sim_val', 'rate_sim_score']], on='restaurant_id')
    # Drop interim values that are no longer needed
    like_restaurants = like_restaurants.drop(['max', 'min'], axis=1)

    # 4) Calculate number of shared restaurant reviews
    # Review similarity = N/10 (this will help get more 1-2 order interconnectons)
    def shared(df):
        return round(min((float(df['shared_val']) / 10), 1), 2)

    like_restaurants['shared_score'] = like_restaurants.apply(shared, axis=1)

    # 5) Calculate restaurant overlap considering total reviews of both restaurants
    # Create column for combined reviews of both users
    def combined(df):
        return str(df['shared_val']) + ' / ' + str(df['reviews'] + df['sel_reviews'])

    like_restaurants['overlap_val'] = like_restaurants.apply(combined, axis=1)

    # Review overlap = # shared / logn(combined review count)   but not greater than one
    def overlap(df):
        return round(min((df['shared_val'] / (5 * math.log(df['reviews'] + df['sel_reviews']))), 1), 2)

    like_restaurants['overlap_score'] = like_restaurants.apply(overlap, axis=1)

    # 6) Calculate jaccard similarity of review counts
    # Review count similarity = logn(min count)/ logn(max count)
    def review_sim(df):
        return round(math.log(min(df['reviews'], df['sel_reviews'])) / math.log(max(df['reviews'], df['sel_reviews'])),2)

    like_restaurants['review_sim_score'] = like_restaurants.apply(review_sim, axis=1)

    # Record the value used to calculate the review count similarity
    def review_sim_val(df):
        return str(min(df['reviews'], df['sel_reviews'])) + ' / ' + str(max(df['reviews'], df['sel_reviews']))

    like_restaurants['review_sim_val'] = like_restaurants.apply(review_sim_val, axis=1)
    like_restaurants = like_restaurants.drop(['reviews', 'sel_reviews'], axis=1)

    # 7) Calculate zip code match (yes/no)
    # a if condition else b
    def zip_score(df):
        return 1 if (df['zip'] == df['sel_zip']) else 0

    like_restaurants['zip_score'] = like_restaurants.apply(zip_score, axis=1)

    # Record the yes/no value
    def zip_val(df):
        return 'Yes' if (df['zip'] == df['sel_zip']) else 'No'

    like_restaurants['zip_val'] = like_restaurants.apply(zip_val, axis=1)
    like_restaurants = like_restaurants.drop(['zip', 'sel_zip'], axis=1)

    # 8) Calculate overall competitive similarity score
    # competitive similarity= User ratings similarity + # Shared reviewing users + Total reviewers overlap
    #     + Review count similarity + Zip code match
    def compete_score(df):
        return round((df['rate_sim_score'] + df['shared_score'] + df['overlap_score'] + df['review_sim_score'] + df[
            'zip_score']), 2)

    like_restaurants['compete_score'] = like_restaurants.apply(compete_score, axis=1)

    # 9) Group by userid to clip at specified limit
    # Note: Taking max of LMU_score to get it into a dataframe
    limited = like_restaurants.groupby('restaurant_id').agg({'compete_score': 'max'}).reset_index()
    limited.sort_values(['compete_score'], ascending=False, inplace=True)
    # Note that Pandas does not reindex after sorting; If we don't reindex explictly, limit may choose unordered rows!!
    limited.reset_index(drop=True, inplace=True)
    # Join the competitor similarity score on the like restaurants list (duplicating score on multiple user records)
    # Inner join to remove restaurants that are beyond the limit
    like_restaurants = pd.merge(like_restaurants, limited.loc[0:limit, ['restaurant_id']], on='restaurant_id',
                                how='inner')

    # 10) Order columns by the Like Minded User Similarity table they will fill
    like_restaurants = like_restaurants[['user', 'user_id', 'restaurant', 'restaurant_id', 'sel_rating', \
                       'shared_val', 'shared_score', 'overlap_val', 'overlap_score', 'review_sim_val', 'review_sim_score', \
                       'rate_sim_val', 'rate_sim_score', 'zip_val', 'zip_score', 'compete_score']]

    # 11) Order by LMU similarity
    like_restaurants.sort_values(['compete_score', 'restaurant_id'], ascending=False, inplace=True)
    like_restaurants.reset_index(drop=True, inplace=True)

    return like_restaurants


# RECOMMENDED_RESTAURANTS returns all information to build out recommended restaurant third-order nodes.
# Also contains information to build comparison bar graph of third order recommended restaurants.
def recommended_restaurants(like_users_df, limit):
    # First, get a listing of unique first-order restaurants and second-order like-minded users
    # Note: like_users df will have duplicate restaurant rows and user rows, so must de-duped!
    restaurant_ids = like_users_df.loc[:, ['restaurant_id']].drop_duplicates(subset=['restaurant_id'])
    user_ids = like_users_df.loc[:, ['user_id']].drop_duplicates(subset=['user_id'])

    # Convert to list and then to a tuple that can be used for SQL "IN"
    restaurant_ids = restaurant_ids.loc[:, 'restaurant_id'].values.tolist()   # Why do I have to slice it again to make it work?
    restaurant_ids = [str(item) for item in restaurant_ids]      # Drop the dreaded unicode label
    if len(restaurant_ids) == 1:
        restaurant_ids = "('"+ restaurant_ids[0] + "')"        # Avoid tuple trailing comma for single elements
    else:
        restaurant_ids = tuple(restaurant_ids)
    user_ids = user_ids.loc[:, 'user_id'].values.tolist()  # Convert dataframe to list
    user_ids = [str(item) for item in user_ids]           # Drop the dreaded unicode label
    if len(user_ids) == 1:
        user_ids = "('"+ user_ids[0] + "')"             # Avoid tuple trailing comma for single elements
    else:
        user_ids = tuple(user_ids)

    # Query for all Yelp restaurants reviewed by the second-order like-minded users
    # Note: First-order restaurants are excluded becuase we don't want to recommend a restaurant already reviewed by active user
    # Ordered by most popular (highest avg rating) restaurants in case more than 2000 records returned
    sql = """SELECT b.name AS restaurant, b.id AS restaurant_id, b.stars AS avg_rating,
          u.name AS user, r.user_id, r.stars AS lmu_rating
          FROM review AS r JOIN business AS b ON r.business_id = b.id 
          JOIN user AS u on r.user_id = u.id
          WHERE r.user_id IN {xxx} AND r.business_id NOT IN {yyy}
          ORDER BY b.stars DESC LIMIT 2000"""
    sql = sql.format(xxx=user_ids, yyy=restaurant_ids)
    reco_restaurants = pd.read_sql(sql, engine)

    # Add LMU user similarity score to the dataframe
    # Note: like_users_df has duplicate userids, so need to de-dup first!
    lmu_score = like_users_df.loc[:, ['user_id', 'lmu_score']].drop_duplicates(subset=['user_id'])
    reco_restaurants = pd.merge(reco_restaurants, lmu_score, on='user_id')

    # Calculate LMU rating weighted by their LMU similarity scores
    def weighted_rel(df):
        return round((float(df['lmu_rating']) * df['lmu_score']), 2)

    reco_restaurants['contribution'] = reco_restaurants.apply(weighted_rel, axis=1)

    # Aggregate on restaurant_id to sum the subscores and the lmu_scores, and count the number of votes
    # Note: Taking max of avg_rating just to get its value into the relevance table
    relevance = reco_restaurants.groupby('restaurant_id') \
        .agg({'user_id': 'size', 'avg_rating': 'max', 'lmu_score': 'sum', 'contribution': 'sum'}) \
        .rename(columns={'user_id': 'reviewers', 'lmu_score': 'sum_lmu_score', 'contribution': 'sum_contribution'}) \
        .reset_index()

    # FYI - These work:
    # relevance = reco_restaurants.groupby(['restaurant_id'], as_index=False)['lmu_score', 'rel_subscore'].sum()
    # reco_restaurants = reco_restaurants.drop_duplicates(subset=['restaurant_id'])

    # Normalize subscore sum by dividing by sum of the lmu scores
    # ADAPTIVE ALGORITHM EXAMPLE:
    # If a restaurant had only one vote, then equally average in the average rating across all reviewers
    # a if condition else b
    def rel_score(df):
        # Alternative A: Always include average rating in calculation
        # return round(((df['avg_rating']*5 + df['sum_contribution'])/(df['sum_lmu_score'] + 5)),2)
        # Alternative B: If a restaurant had only one vote, then include its average rating, weighted at maximum 5
        return round((df['sum_contribution'] / df['sum_lmu_score']) if (df['reviewers'] > 1) else \
                         ((df['avg_rating'] * 5 + df['sum_contribution']) / (df['sum_lmu_score'] + 5)), 2)

    relevance['relevancy'] = relevance.apply(rel_score, axis=1)

    # Order the relevancy table and limit it
    # Note that limit is applied here on list of unique restaurants, not on the duplicated restaurant list
    relevance.sort_values(['relevancy'], ascending=False, inplace=True)
    # Also note that Pandas does not reindex after sorting; If we don't do it explictly, limit will choose unordered rows!!
    relevance.reset_index(drop=True, inplace=True)
    rel_calc = relevance.loc[0:limit, ['restaurant_id', 'relevancy']]

    # Join the relevancy score on the recommended restaurant list (duplicating score on multiple user records)
    # Inner join to remove restaurants that are beyond the limit
    reco_restaurants = pd.merge(reco_restaurants, rel_calc, on='restaurant_id', how='inner')

    # Order dataframe by relevancy score
    reco_restaurants.sort_values(['relevancy', 'restaurant_id'], ascending=False, inplace=True)
    reco_restaurants.reset_index(drop=True, inplace=True)

    return reco_restaurants


# CUSTOMER_PROPSECTS returns all information to build out customer prospect third order nodes.
# Also contains information to build comparison bar graph of all first order rating users,
#    second order direct competitor restaurants, and third order customer prospect users.
def customer_prospects(like_restaurants_df, limit):
    # First, get a listing of unique first-order reviewers and second-order restaurant competitors
    # Note: like_restaurants df will have duplicate restaurant rows and user rows, so must de-duped!
    user_ids = like_restaurants_df.loc[:, ['user_id']].drop_duplicates(subset=['user_id'])
    restaurant_ids = like_restaurants_df.loc[:, ['restaurant_id']].drop_duplicates(subset=['restaurant_id'])

    # Convert to list and then to a tuple that can be used for SQL "IN"
    restaurant_ids = restaurant_ids.loc[:, 'restaurant_id'].values.tolist()   # Why do I have to slice it again to make it work?
    restaurant_ids = [str(item) for item in restaurant_ids]      # Drop the dreaded unicode label
    if len(restaurant_ids) == 1:
        restaurant_ids = "('"+ restaurant_ids[0] + "')"        # Avoid tuple trailing comma for single elements
    else:
        restaurant_ids = tuple(restaurant_ids)
    user_ids = user_ids.loc[:, 'user_id'].values.tolist()  # Convert dataframe to list
    user_ids = [str(item) for item in user_ids]           # Drop the dreaded unicode label
    if len(user_ids) == 1:
        user_ids = "('"+ user_ids[0] + "')"             # Avoid tuple trailing comma for single elements
    else:
        user_ids = tuple(user_ids)

    # Query for all the users who reviewed these 2nd order restaurants
    # Note: First-order reviewers are excluded - don't recommend a prospect who has already reviewed the active restaurant
    # Ordered by most useful reviewers in case more than 1000 records returned
    sql = """SELECT u.name AS user, u.id AS user_id, u.average_stars AS avg_rating,
          b.name AS restaurant, r.business_id AS restaurant_id, r.stars AS user_rating
          FROM review AS r JOIN business AS b ON r.business_id = b.id 
          JOIN user AS u on r.user_id = u.id
          WHERE r.business_id IN {xxx} AND r.user_id NOT IN {yyy}
          ORDER BY u.useful DESC LIMIT 1000"""
    sql = sql.format(xxx=restaurant_ids, yyy=user_ids)
    customer_prospects = pd.read_sql(sql, engine)

    # Add competitor similarity score to the dataframe
    # Note: like_restaurants_df has duplicate restaurant_ids, so need to de-dup first!
    compete_score = like_restaurants_df.loc[:, ['restaurant_id', 'compete_score']].drop_duplicates(
        subset=['restaurant_id'])
    customer_prospects = pd.merge(customer_prospects, compete_score, on='restaurant_id')

    # Calculate user's ratings of competitors weighted by their competitive similarity scores
    def weighted_rel(df):
        return round((float(df['user_rating']) * df['compete_score']), 2)

    customer_prospects['contribution'] = customer_prospects.apply(weighted_rel, axis=1)

    # Aggregate on user_id to sum the contributions and the compete_scores, and count the number of user's reviews
    # Note: Taking max of avg_rating just to get it into the relevance df
    relevance = customer_prospects.groupby('user_id') \
        .agg({'restaurant_id': 'size', 'avg_rating': 'max', 'compete_score': 'sum', 'contribution': 'sum'}) \
        .rename(
        columns={'restaurant_id': 'reviewed', 'compete_score': 'sum_compete_score', 'contribution': 'sum_contribution'}) \
        .reset_index()

    # Normalize contribution sum by dividing by sum of the compete scores
    # If a user had only one review, then equally average in his average rating across all restaurants???
    # ***DMT: I don't think this is an issue on the restaurant side (rare for restaurant to have only one review)
    def rel_score(df):
        # Alteternative A: Only consider a user's ratings of each restaurant
        # return round((df['sum_contribution']/df['sum_compete_score']),2)
        # Alternative B: If user reviewed only one restaurant, then include user's overall average rating, weighted at maximum 5
        return round((df['sum_contribution'] / df['sum_compete_score']) if (df['reviewed'] > 1) else \
                         ((df['avg_rating'] * 5 + df['sum_contribution']) / (df['sum_compete_score'] + 5)), 2)

    relevance['relevancy'] = relevance.apply(rel_score, axis=1)

    # Order the relevancy table and limit it
    # Note that limit is applied here on list of unique restaurants, not on the duplicated restaurant list
    relevance.sort_values(['relevancy'], ascending=False, inplace=True)
    # Also note that Pandas does not reindex after sorting; If we don't do it explictly, limit will choose unordered rows!!
    relevance.reset_index(drop=True, inplace=True)
    rel_calc = relevance.loc[0:limit, ['user_id', 'reviewed', 'relevancy']]

    # Join the relevancy score on the recommended restaurant list (duplicating score on multiple restaurant records)
    # Inner join to remove users that are beyond the limit
    customer_prospects = pd.merge(customer_prospects, rel_calc, on='user_id', how='inner')

    # Order dataframe by relevancy score
    customer_prospects.sort_values(['relevancy', 'user_id'], ascending=False, inplace=True)
    customer_prospects.reset_index(drop=True, inplace=True)

    return customer_prospects


# USER GRAPH creates global nodes and links dataframes to build the active user node graph
def user_graph(active_user_id, user_profile_df, like_users_df, recommended_restaurants_df):
    # How to build dataframes to represent the graph
    # Begin with objective in mind: JSON structure
    # "nodes": [{
    #      "id": "id1",
    #      "name": "Rest1-1",
    #      "type": "restaurant",
    #      "order": "2"
    #      "score": "3.9"
    # }],
    # "links": [ {
    #      "source": "id1",
    #      "target": "id2",
    #      "src_order": "2",
    #      "score": "2.7"
    # }]

    # New dataframes to contain the user graph information
    nodes = pd.DataFrame()
    links = pd.DataFrame()

    # Get information for second to third order links
    linkset = recommended_restaurants_df.loc[:, ['user_id', 'restaurant_id', 'lmu_rating']]
    linkset.rename(columns={'user_id': 'source', 'restaurant_id': 'target', 'lmu_rating': 'score'}, inplace=True)
    # Record the orders of the nodes (counting outward from active_user = 0)
    linkset['src_order'] = 2
    # Append to the links df
    links = links.append(linkset, ignore_index=True)

    # Get unique third order restaurant information for nodes df
    nodeset = recommended_restaurants_df.loc[:, ['restaurant_id', 'restaurant', 'relevancy']].drop_duplicates(
        subset=['restaurant_id'])
    nodeset.rename(columns={'restaurant_id': 'id', 'restaurant': 'name', 'relevancy': 'score'}, inplace=True)
    nodeset['type'] = 'restaurant'
    nodeset['order'] = 3
    # Append to the nodes df
    nodes = nodes.append(nodeset, ignore_index=True)

    # Get unique second order user information for nodes df
    nodeset = recommended_restaurants_df.loc[:, ['user_id', 'user', 'lmu_score']].drop_duplicates(subset=['user_id'])
    nodeset.rename(columns={'user_id': 'id', 'user': 'name', 'lmu_score': 'score'}, inplace=True)
    nodeset['type'] = 'user'
    nodeset['order'] = 2
    # Append to the nodes df
    nodes = nodes.append(nodeset, ignore_index=True)

    # Get the subset of second-order like-minded users that had reviewed the most relevant third-order restaurants
    # We do this by applying an inner join of the second order users in reco_restaurants to the users in like_minded_users
    nodeset.rename(columns={'id': 'user_id'}, inplace=True)
    second_order_users = pd.merge(nodeset, like_users_df, on='user_id', how='inner')  # Will this ever reduce???

    # Get information for first to second order links
    linkset = second_order_users.loc[:, ['restaurant_id', 'user_id', 'sel_rating']]
    linkset.rename(columns={'restaurant_id': 'source', 'user_id': 'target', 'sel_rating': 'score'}, inplace=True)
    # Record the orders of the nodes (counting outward from active_user = 0)
    linkset['src_order'] = 1
    # Append to the links df
    links = links.append(linkset, ignore_index=True)

    # Get info on the subset of first-order restaurants reviewed by the chosen like-minded users
    # First, capture their id's for SQL query
    second_order_users.drop_duplicates(subset=['restaurant_id'], inplace=True)
    ids = second_order_users.loc[:, 'restaurant_id'].values.tolist()
    in_ids = [str(item) for item in ids]           # Drop the dreaded unicode label
    if len(in_ids) == 1:
        in_ids = "('"+ in_ids[0] + "')"             # Avoid tuple trailing comma for single elements
    else:
        in_ids = tuple(in_ids)

    # Query for the ratings the active user gave these restaurants
    # **** DMT: Assign value to active_user_id!!!!!!!
    print(active_user_id)
    sql = """SELECT b.id, b.name, r.stars AS score
              FROM review AS r JOIN business AS b ON r.business_id = b.id 
              WHERE r.user_id = '{xxx}' AND b.id IN {yyy}"""
    sql = sql.format(xxx=active_user_id, yyy=in_ids)
    nodeset = pd.read_sql(sql, engine)
    nodeset['type'] = 'restaurant'
    nodeset['order'] = 1
    # Add the first-order restaurants to the nodes df
    nodes = nodes.append(nodeset, ignore_index=True)

    # Create links from the active user to these first-order restaurants
    linkset = nodeset.loc[:, ['id', 'score']]
    linkset.rename(columns={'id': 'target'}, inplace=True)
    linkset['source'] = active_user_id
    linkset['src_order'] = 0
    # Append to the links df
    links = links.append(linkset, ignore_index=True)
    # Keep links columns in preferred order
    links = links[['source', 'target', 'src_order', 'score']]

    # Finally, add the active user node to the nodes df
    newrow = {}
    newrow['id'] = active_user_id  # user_profile_df['user_id']
    newrow['name'] = user_profile_df['name'].iloc[0]
    newrow['score'] = -1  # Default value for active node
    newrow['type'] = 'user'
    newrow['order'] = 0
    nodes = nodes.append(newrow, ignore_index=True)
    # Keep nodes columns in preferred order
    nodes = nodes[['id', 'name', 'type', 'order', 'score']]

    # Package the two dataframes into a dictionary
    graph = {'nodes': nodes, 'links': links}

    return graph


# RESTAURANT_GRAPH creates global nodes and links dataframes to build the active restaurant node graph

def restaurant_graph(active_restaurant_id, restaurant_profile_df, like_restaurants_df, customer_prospects_df):
    # New dataframes to contain the restaurant graph information
    nodes = pd.DataFrame()
    links = pd.DataFrame()

    # Get information for second to third order links
    linkset = customer_prospects_df.loc[:, ['restaurant_id', 'user_id', 'compete_score']]
    linkset.rename(columns={'restaurant_id': 'source', 'user_id': 'target', 'compete_score': 'score'}, inplace=True)
    # Record the orders of the nodes (counting outward from active_user = 0)
    linkset['src_order'] = 2
    # Append to the links df
    links = links.append(linkset, ignore_index=True)

    # Get unique third order user information for nodes df
    nodeset = customer_prospects_df.loc[:, ['user_id', 'user', 'relevancy']].drop_duplicates(subset=['user_id'])
    nodeset.rename(columns={'user_id': 'id', 'user': 'name', 'relevancy': 'score'}, inplace=True)
    nodeset['type'] = 'user'
    nodeset['order'] = 3
    # Append to the nodes df
    nodes = nodes.append(nodeset, ignore_index=True)

    # Get unique second order restaurant information for nodes df
    nodeset = customer_prospects_df.loc[:, ['restaurant_id', 'restaurant', 'compete_score']].drop_duplicates(
        subset=['restaurant_id'])
    nodeset.rename(columns={'restaurant_id': 'id', 'restaurant': 'name', 'compete_score': 'score'}, inplace=True)
    nodeset['type'] = 'restaurant'
    nodeset['order'] = 2
    # Append to the nodes df
    nodes = nodes.append(nodeset, ignore_index=True)

    # Get the subset of second-order direct competitors reviewed by the most relevant third-order users
    # We do this by applying an inner join of the second order restaurants in customer_prospects to the restaurants in like_restaurants
    nodeset.rename(columns={'id': 'restaurant_id'}, inplace=True)
    second_order_users = pd.merge(nodeset, like_restaurants_df, on='restaurant_id', how='inner')  # Will this ever reduce???

    # Get information for first to second order links
    linkset = second_order_users.loc[:, ['user_id', 'restaurant_id', 'sel_rating']]
    linkset.rename(columns={'user_id': 'source', 'restaurant_id': 'target', 'sel_rating': 'score'}, inplace=True)
    # Record the orders of the nodes (counting outward from active_user = 0)
    linkset['src_order'] = 1
    # Append to the links df
    links = links.append(linkset, ignore_index=True)

    # Get info on the subset of first-order users who reviewed the chosen direct competitors
    # First, capture their id's for SQL query
    second_order_users.drop_duplicates(subset=['user_id'], inplace=True)
    ids = second_order_users.loc[:, 'user_id'].values.tolist()
    in_ids = [str(item) for item in ids]           # Drop the dreaded unicode label
    if len(in_ids) == 1:
        in_ids = "('"+ in_ids[0] + "')"             # Avoid tuple trailing comma for single elements
    else:
        in_ids = tuple(in_ids)

    # Query for the ratings the active restaurant received from these users
    sql = """SELECT u.id, u.name, r.stars AS score
              FROM review AS r JOIN user AS u ON r.user_id = u.id 
              WHERE r.business_id = '{xxx}' AND r.user_id IN {yyy}"""
    sql = sql.format(xxx=active_restaurant_id, yyy=in_ids)
    nodeset = pd.read_sql(sql, engine)
    nodeset['type'] = 'user'
    nodeset['order'] = 1
    # Add the first-order restaurants to the nodes df
    nodes = nodes.append(nodeset, ignore_index=True)

    # Create links from the active restaurant to these first-order users
    linkset = nodeset.loc[:, ['id', 'score']]
    linkset.rename(columns={'id': 'target'}, inplace=True)
    linkset['source'] = active_restaurant_id
    linkset['src_order'] = 0
    # Append to the links df
    links = links.append(linkset, ignore_index=True)
    # Keep links columns in preferred order
    links = links[['source', 'target', 'src_order', 'score']]

    # Finally, add the active restaurant node to the nodes df
    nodeset = pd.DataFrame()
    nodeset['id'] = restaurant_profile_df['restaurant_id']
    nodeset['name'] = restaurant_profile_df['name']
    nodeset['score'] = -1  # Default value for active node
    nodeset['type'] = 'restaurant'
    nodeset['order'] = 0
    nodes = nodes.append(nodeset, ignore_index=True)
    # Keep nodes columns in preferred order
    nodes = nodes[['id', 'name', 'type', 'order', 'score']]

    # Package the two dataframes into a dictionary
    graph = {'nodes': nodes, 'links': links}

    return graph


