# -*- coding: utf-8 -*-
# These functions are called from View.py and in turn call modules in algorithm.py

import logging

import pandas as pd

from bipolo import (
    db, algorithm
)

# Engine is the key to executing raw sql
engine = db.engine

# ***********Setup Global Variables************
fo_limit = 10                      # 1st order node limits
lmu_limit = 20                     # 2nd order node limits
competitor_limit = 20
reco_limit = 30                    # 3rd order node limits
prospect_limit = 30
like_limit = 10                    # Like nodes on left side

# **********  SEARCH MODE API CALLS  **********

# SEARCH is called when the magnifying glass icon is clicked with a non-empty search field.
# Parms: string = alphanumeric characters that restaurant names must begin with
def search(string,limit):

    results = algorithm.search(string, limit)

    return results


# FULL_LIST is called at initialization to give a full list of Phoenix restaurants and restaurant_ids to the Frontend
# Frontend code will cache the list for local search handling
# Parms: NONE!
def full_list():
    results = algorithm.full_list()

    return results


# **********  EXPLORE MODE API CALLS  **********

# USER_PROFILE is called in explore mode when a user node is clicked.
# Parms: user_id = id of active user node
def user_profile(user_id):
    # Get details for profile window
    user_profile_df = algorithm.user_profile(user_id)
    # Note: Full conversion to string with .astype(str) has been commented out throughout API.py to fix issue #7
    #user_profile_str_df = user_profile_df.astype(str)
    user_profile_str_df = user_profile_df

    # Get first/second order nodes for graph, and info for like nodes across bottom of page
    like_users_df = algorithm.like_users(user_profile_df, user_id, lmu_limit)
    #like_users_str_df = like_users_df[['user', 'user_id', 'lmu_score']].astype(str).drop_duplicates().head(like_limit)   # Issue #7
    like_users_str_df = like_users_df[['user', 'user_id', 'lmu_score']].drop_duplicates().head(like_limit)

    # Get third order nodes for graph
    recommended_restaurants_df = algorithm.recommended_restaurants(like_users_df, reco_limit)
    # display(recommended_restaurants_df)

    # Transform graph info into nodes and links lists
    user_graph_dict = algorithm.user_graph(user_id, user_profile_df, like_users_df, recommended_restaurants_df)

    return user_profile_str_df, user_graph_dict, like_users_str_df


# RESTAURANT_PROFILE is called in explore mode when a restaurant node is clicked.
# Parms: restaurant_id = id of active restaurant node
def restaurant_profile(restaurant_id):

    # Get details for profile window
    restaurant_profile_df = algorithm.restaurant_profile(restaurant_id)
    #restaurant_profile = restaurant_profile_df.astype(str)        # Issue #7
    restaurant_profile = restaurant_profile_df

    # Get first/second order nodes for graph, and info for like nodes across bottom of page
    like_restaurants_df = algorithm.like_restaurants(restaurant_id, competitor_limit)
    #like_restaurants_str_df = like_restaurants_df[['restaurant', 'restaurant_id', 'compete_score']].astype(str).drop_duplicates().head(like_limit)     # Issue #7
    like_restaurants_str_df = like_restaurants_df[['restaurant', 'restaurant_id', 'compete_score']].drop_duplicates().head(like_limit)

    # Get third order nodes for graph
    customer_prospects_df = algorithm.customer_prospects(like_restaurants_df, prospect_limit)

    # Transform graph info into nodes and links lists
    restaurant_graph_dict = algorithm.restaurant_graph(restaurant_id, restaurant_profile_df, like_restaurants_df,
                                                       customer_prospects_df)

    return restaurant_profile, restaurant_graph_dict, like_restaurants_str_df


# **********  ANALYSIS MODE API CALLS  **********     # All analysis calls below are assuming the frontend can cache the active node profile
                                                      # If not, we'll need to return profile also

# RATING_OF_RESTAURANT is called when a first-order restaurant node is clicked.
# Parms: active_user_id = id of the active user
#        restaurant _id = id of the selected first-order restaurant
def rating_of_restaurant(active_user_id, restaurant_id):
    # Get active user info for other routines
    user_profile_df = algorithm.user_profile(active_user_id)
    #user_profile = user_profile_df.astype(str)       # Issue #7
    #user_profile = user_profile_df

    # Get first/second order nodes for graph
    like_users_df = algorithm.like_users(user_profile_df, active_user_id, lmu_limit)

    # Get third order nodes for graph
    recommended_restaurants_df = algorithm.recommended_restaurants(like_users_df, reco_limit)
    # display(recommended_restaurants_df)

    # Transform graph info into nodes and links lists
    user_graph_dict = algorithm.user_graph(active_user_id, user_profile_df, like_users_df, recommended_restaurants_df)

    nodes = user_graph_dict['nodes']
    nodes_comparison = nodes[nodes['order'] == 1][['name', 'score']]
    nodes_comparison.sort_values(by = ['score'],ascending =False,inplace = True)
    nodes_comparison = nodes_comparison.round({'score':2})

    # Returns details of how active user rated restaurant
    rating_df = algorithm.user_restaurant_rating(active_user_id, restaurant_id)
    #rating = rating_df[['restaurant', 'user', 'rating', 'date', 'review', 'useful', 'funny', 'cool']].astype(str)   # Issue #7
    rating = rating_df[['restaurant', 'user', 'rating', 'date', 'review', 'useful', 'funny', 'cool']]

    # return the likes nodes at the bottom            # Also use algorithm.like_restaurants for comparison bar graph
    like_restaurants_df = algorithm.like_restaurants(restaurant_id, competitor_limit)
    like_restaurants_df['restaurant'] = like_restaurants_df['restaurant'].str.encode('utf8')
    like_restaurants_str_df = like_restaurants_df[['restaurant', 'restaurant_id', 'compete_score']].astype(
        str).drop_duplicates().head(like_limit)             # Issue #7

                          # Return doesn't match View.py which will expect graph_dict, like, rating, comparison
    return rating, nodes_comparison, like_restaurants_str_df


# RATING_BY_USER is called when a first-order user node is clicked.
# Parms:  active_restaurant_id = id of the active restaurant
#         user _id = id of the selected first-order user

def rating_by_user(active_restaurant_id, user_id):
    # Get active restaurant info for other routines
    restaurant_profile_df = algorithm.restaurant_profile(active_restaurant_id)
    #restaurant_profile = restaurant_profile_df.astype(str)       # Issue #7
    #restaurant_profile = restaurant_profile_df

    # Get first/second order nodes for graph
    like_restaurants_df = algorithm.like_restaurants(active_restaurant_id, competitor_limit)

    # Get third order nodes for graph
    customer_prospects_df = algorithm.customer_prospects(like_restaurants_df, prospect_limit)

    # Transform graph info into nodes and links lists
    restaurant_graph_dict = algorithm.restaurant_graph(active_restaurant_id, restaurant_profile_df, like_restaurants_df,
                                                       customer_prospects_df)

    # Get info for comparison bar graph
    nodes = restaurant_graph_dict['nodes']
    nodes_comparison = nodes[nodes['order'] == 1][['name', 'score']]
    nodes_comparison.sort_values(by = ['score'],ascending =False,inplace = True)
    nodes_comparison = nodes_comparison.round({'score':2})


    # Returns details of how active restaurant was rated by selected user
    rating_df = algorithm.user_restaurant_rating(user_id, active_restaurant_id)
    #rating_str_df = rating_df[['restaurant', 'user', 'rating', 'date', 'review', 'useful', 'funny', 'cool']].astype(str)      # Issue #7
    rating_str_df = rating_df[['restaurant', 'user', 'rating', 'date', 'review', 'useful', 'funny', 'cool']]

    ## Get info for like nodes across bottom of page
    user_profile_df = algorithm.user_profile(user_id)
    like_users_df = algorithm.like_users(user_profile_df, user_id, lmu_limit)
    #like_users_str_df = like_users_df[['user', 'user_id', 'lmu_score']].astype(str).drop_duplicates().head(like_limit)        # Issue #7
    like_users_str_df = like_users_df[['user', 'user_id', 'lmu_score']].drop_duplicates().head(like_limit)

                       # Return should be: restaurant_graph_dict, like_users, rating, nodes_comparison
    return rating_str_df, nodes_comparison, like_users_str_df


# LIKEMINDED_USER_SIMILARITY is called when a second-order user node is clicked.
# Parms: active_user_id = id of the active user
#        selected_user _id = id of the selected second-order user

def likeminded_user_similarity(active_user_id, selected_user_id):

    # Get active user info for other routines
    active_user_profile_df = algorithm.user_profile(active_user_id)
    #user_profile = active_user_profile_df.astype(str)                # Issue #7
    #user_profile = active_user_profile_df

    # Get first/second order nodes for graph
    active_like_users_df = algorithm.like_users(active_user_profile_df, active_user_id, lmu_limit)

    # Pull off details on selected LMU for upper right window
    #LMU_similarity = active_like_users_df[active_like_users_df['user_id'] == selected_user_id][
    #    ['shared_val', 'shared_score', 'overlap_val', 'overlap_score', 'rate_sim_val', 'rate_sim_score',
    #     'influence_val', 'influence_score', 'influ_sim_val', 'influ_sim_score', 'lmu_score']].astype(str)        # Issue #7
    LMU_similarity = active_like_users_df[active_like_users_df['user_id'] == selected_user_id][
        ['shared_val', 'shared_score', 'overlap_val', 'overlap_score', 'rate_sim_val', 'rate_sim_score',
         'influence_val', 'influence_score', 'influ_sim_val', 'influ_sim_score', 'lmu_score']]

    # Get third order nodes for graph
    recommended_restaurants_df = algorithm.recommended_restaurants(active_like_users_df, reco_limit)
    # display(recommended_restaurants_df)

    # Transform graph info into nodes and links lists
    user_graph_dict = algorithm.user_graph(active_user_id, active_user_profile_df, active_like_users_df,
                                           recommended_restaurants_df)

    # Get info for comparison bar graph
    nodes = user_graph_dict['nodes']
    nodes_comparison = nodes[nodes['order'] == 2][['name', 'score']]
    nodes_comparison.sort_values(by = ['score'],ascending =False,inplace = True)
    nodes_comparison = nodes_comparison.round({'score':2})



    # Prepare the like user nodes
    selected_user_profile_df = algorithm.user_profile(selected_user_id)
    like_users_df = algorithm.like_users(selected_user_profile_df, selected_user_id, lmu_limit)
    #like_users_str_df = like_users_df[['user', 'user_id', 'lmu_score']].astype(str).drop_duplicates().head(like_limit)     # Issue #7
    like_users_str_df = like_users_df[['user', 'user_id', 'lmu_score']].drop_duplicates().head(like_limit)

                                       # user_graph_dict, like_users, LMU_similarity, nodes_comparison
    return LMU_similarity, nodes_comparison, like_users_str_df


# DIRECT_COMPETITOR_SIMILARITY is called when a second-order restaurant node is clicked.
# Parms: active_restaurant_id = id of the active restaurant
#        selected_restaurant_id = id of the selected second-order restaurant

def direct_competitor_similarity(active_restaurant_id, selected_restaurant_id):
    # Get active restaurant info for other routines
    active_restaurant_profile_df = algorithm.restaurant_profile(active_restaurant_id)
    #restaurant_profile = active_restaurant_profile_df.astype(str)                   # Issue #7
    #restaurant_profile = active_restaurant_profile_df

    # Get first/second order nodes for graph
    active_like_restaurants_df = algorithm.like_restaurants(active_restaurant_id, competitor_limit)

    # Pull off details on selected direct competitor similarity for upper right window
    restaurant_similarity = active_like_restaurants_df[active_like_restaurants_df['restaurant_id'] == selected_restaurant_id][['shared_val', 'shared_score', 'overlap_val', 'overlap_score', 'review_sim_val','review_sim_score','rate_sim_val', 'rate_sim_score', 'zip_val',
         'zip_score', 'compete_score']]

    # Get third order nodes for graph
    customer_prospects_df = algorithm.customer_prospects(active_like_restaurants_df, prospect_limit)

    # Transform graph info into nodes and links lists
    restaurant_graph_dict = algorithm.restaurant_graph(active_restaurant_id, active_restaurant_profile_df,
                                                       active_like_restaurants_df, customer_prospects_df)

    # Get info for comparison bar graph
    nodes = restaurant_graph_dict['nodes']                      # Call these nodes and nodes_comparison
    nodes_comparison = nodes[nodes['order'] == 2][['name', 'score']]
    nodes_comparison.sort_values(by = ['score'],ascending =False,inplace = True)
    nodes_comparison = nodes_comparison.round({'score':2})


    ##likes
    restaurant_profile_df = algorithm.restaurant_profile(selected_restaurant_id)     # Not needed - delete

    # Prepare the like user nodes
    like_restaurants_df = algorithm.like_restaurants(selected_restaurant_id, competitor_limit)[['restaurant', 'restaurant_id', 'compete_score']]
    like_restaurants_df['restaurant'] = like_restaurants_df['restaurant'].str.encode('utf8')
    like_restaurants_df['restaurant_id'] = like_restaurants_df['restaurant_id'].str.encode('utf8')
    like_restaurants_df['compete_score'] = like_restaurants_df['compete_score'].astype(str)
    like_restaurants_df = like_restaurants_df.drop_duplicates().head(like_limit)               # Issue #7
    return restaurant_similarity, nodes_comparison, like_restaurants_df


# RECOMMENDED_RESTAURANT_RELEVANCE is called when a third-order restaurant node is clicked.
# Parms: active_user_id = id of the active user
#        selected_restaurant _id = id of the selected third-order restaurant

def recommended_restaurant_relevance(active_user_id, selected_restaurant_id):
    # Get active restaurant info for other routines
    active_user_profile_df = algorithm.user_profile(active_user_id)
    #user_profile = active_user_profile_df.astype(str)              # Issue #7
    #user_profile = active_user_profile_df

    # Get first/second order nodes for graph
    active_like_users_df = algorithm.like_users(active_user_profile_df, active_user_id, lmu_limit)

    # Get third order nodes for graph
    recommended_restaurants_df = algorithm.recommended_restaurants(active_like_users_df, reco_limit)

    # Transform graph info into nodes and links lists
    user_graph_dict = algorithm.user_graph(active_user_id, active_user_profile_df, active_like_users_df,
                                           recommended_restaurants_df)

    # Pull off details on selected recommended restaurant relevance for upper right window
    reco_restaurant_relevance = recommended_restaurants_df[recommended_restaurants_df['restaurant_id'] == selected_restaurant_id]
    relevance_df = reco_restaurant_relevance[['user', 'lmu_rating', 'lmu_score', 'contribution', 'relevancy']]
    if (reco_restaurant_relevance.shape[0] == 1):
        avg_rating = reco_restaurant_relevance['avg_rating'].values[0]
        restaurant_similarity = 5.0
        restaurant_contribution = avg_rating * restaurant_similarity
        restaurant_relevancy = reco_restaurant_relevance['relevancy'].values[0]

        restaurant_df = pd.DataFrame(
            {'user': ["Restaurant's Average Rating"], "lmu_rating": [avg_rating], "lmu_score": [restaurant_similarity],
             "contribution": [restaurant_contribution], "relevancy": [restaurant_relevancy]})

        relevance_df = pd.concat([relevance_df, restaurant_df], axis=0)

    #relevance = relevance_df.astype(str)               # Issue #7
    relevance = relevance_df

    # Get info for comparison bar graph
    nodes = user_graph_dict['nodes']
    nodes_comparison = nodes[nodes['order'] == 3][['name', 'score']]    # nodes_comparison
    nodes_comparison.sort_values(by = ['score'],ascending =False,inplace = True)
    nodes_comparison = nodes_comparison.round({'score':2})


    # Prepare the like restaurant nodes
    selected_like_restaurants_df = algorithm.like_restaurants(selected_restaurant_id, competitor_limit)[['restaurant', 'restaurant_id', 'compete_score']]
    selected_like_restaurants_df['restaurant'] = selected_like_restaurants_df['restaurant'].str.encode('utf8')
    selected_like_restaurants_df['restaurant_id'] = selected_like_restaurants_df['restaurant_id'].str.encode('utf8')
    selected_like_restaurants_df['compete_score'] = selected_like_restaurants_df['compete_score'].astype(str)
    selected_like_restaurants_df = selected_like_restaurants_df.drop_duplicates().head(like_limit)               # Issue #7
    return relevance, nodes_comparison, selected_like_restaurants_df


# CUSTOMER_PROSPECT_RELEVANCE is called when a third-order user node is clicked.
# Parms: active_restaurant_id = id of the active restaurant
#        user _id = id of the selected third-order user

def customer_prospect_relevance(active_restaurant_id, selected_user_id):
    # Get active restaurant info for other routines
    active_restaurant_profile_df = algorithm.restaurant_profile(active_restaurant_id)
    #restaurant_profile = active_restaurant_profile_df.astype(str)           # Issue #7
    #restaurant_profile = active_restaurant_profile_df

    # Get first/second order nodes for graph
    active_like_restaurants_df = algorithm.like_restaurants(active_restaurant_id, competitor_limit)

    # Get third order nodes for graph
    customer_prospects_df = algorithm.customer_prospects(active_like_restaurants_df, prospect_limit)

    # Transform graph info into nodes and links lists
    restaurant_graph_dict = algorithm.restaurant_graph(active_restaurant_id, active_restaurant_profile_df, active_like_restaurants_df,
                                                       customer_prospects_df)

    ## Pull off details on selected customer prospect relevance for upper right window
    customer_prospect_relevance = customer_prospects_df[customer_prospects_df['user_id'] == selected_user_id]
    relevance_df = customer_prospect_relevance[['restaurant', 'user_rating', 'compete_score', 'contribution', 'relevancy']]
    if (customer_prospect_relevance.shape[0] == 1):
        avg_rating = customer_prospect_relevance['avg_rating'].values[0]
        user_similarity = 5.0
        user_contribution = avg_rating * user_similarity
        user_relevancy = customer_prospect_relevance['relevancy'].values[0]

        user_df = pd.DataFrame(
            {'restaurant': ["User's Average Rating"], "user_rating": [avg_rating], "compete_score": [user_similarity],
             "contribution": [user_contribution], "relevancy": [user_relevancy]})

        relevance_df = pd.concat([relevance_df, user_df], axis=0)

    #relevance = relevance_df.astype(str)             # Issue #7
    relevance = relevance_df

    # Get info for comparison bar graph
    nodes = restaurant_graph_dict['nodes']
    nodes_comparison = nodes[nodes['order'] == 3][['name', 'score']]
    nodes_comparison.sort_values(by = ['score'],ascending =False,inplace = True)
    nodes_comparison = nodes_comparison.round({'score':2})


    # Prepare the like user nodes
    selected_user_profile_df = algorithm.user_profile(selected_user_id)
    selected_like_users_df = algorithm.like_users(selected_user_profile_df, selected_user_id, lmu_limit)
    #like_users_str_df = selected_like_users_df[['user', 'user_id', 'lmu_score']].astype(str).drop_duplicates().head(like_limit)       # Issue #7
    like_users_str_df = selected_like_users_df[['user', 'user_id', 'lmu_score']].drop_duplicates().head(like_limit)

                               # restaurant_graph_dict, like_users, relevance, nodes_comparison
    return relevance, nodes_comparison, like_users_str_df


# USER_SIMILARITY is called when a user node has been selected and a “like node” is clicked.
# Parms:  selected_user _id = id of the selected user node
#         like_user_id = id of the like user node

def user_similarity(selected_user_id, like_user_id):
    # Get information on the selected user node
    selected_user_profile_df = user_profile(selected_user_id)

    # Get information on all the like nodes and their similarity scores
    selected_like_users_df = algorithm.like_users(selected_user_profile_df, selected_user_id, lmu_limit)

    # Get similarity info on the particular like node that was clicked
    user_similarity = selected_like_users_df[selected_like_users_df['user_id'] == like_user_id]

    #user_similarity_df = user_similarity[
    #    ['shared_val', 'shared_score', 'overlap_val', 'overlap_score', 'rate_sim_val', 'rate_sim_score', 'influence_val',
    #     'influence_score', 'influ_sim_val', 'influ_sim_score', 'lmu_score']].drop_duplicates().astype(str)      # Issue #7
    user_similarity_df = user_similarity[
        ['shared_val', 'shared_score', 'overlap_val', 'overlap_score', 'rate_sim_val', 'rate_sim_score', 'influence_val',
         'influence_score', 'influ_sim_val', 'influ_sim_score', 'lmu_score']].drop_duplicates()

                                             # If Frontend can't preserve graph, then we'll need to include much more
    return user_similarity_df


# RESTAURANT_SIMILARITY is called when a restaurant node has been selected and a “like node” is clicked.
# Parms: selected_restaurant _id = id of the selected user node
#        like_restaurant_id = id of the like user node

def restaurant_similarity(selected_restaurant_id, like_restaurant_id):

    selected_restaurant_profile_df = algorithm.restaurant_profile(selected_restaurant_id)       # Not needed

    # Get information on all the like nodes and their similarity scores
    selected_like_restaurants_df = algorithm.like_restaurants(selected_restaurant_id, competitor_limit)

    # Get similarity info on the particular like node that was clicked
    restaurant_similarity = selected_like_restaurants_df[selected_like_restaurants_df['restaurant_id'] == like_restaurant_id]

    #restaurant_similarity_df = restaurant_similarity[
    #    ['shared_val', 'shared_score', 'overlap_val', 'overlap_score', 'review_sim_val', 'review_sim_score',
    #     'rate_sim_val', 'rate_sim_score', 'zip_val', 'zip_score', 'compete_score']].drop_duplicates().astype(str)   # Issue #7
    restaurant_similarity_df = restaurant_similarity[
        ['shared_val', 'shared_score', 'overlap_val', 'overlap_score', 'review_sim_val', 'review_sim_score',
         'rate_sim_val', 'rate_sim_score', 'zip_val', 'zip_score', 'compete_score']].drop_duplicates()

                                                   # If Frontend can't preserve graph, then we'll need to include much more
    return restaurant_similarity_df
