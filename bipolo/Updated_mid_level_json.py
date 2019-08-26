
# coding: utf-8

# ### YUEGE API INTERFACE BETWEEN PRESENTATION AND ALGORITHM LAYERS 



import logging

import math
import pandas as pd
# from sqlalchemy import select, and_, func

from bipolo import (
    db, algorithm
)

# Engine is the key to executing raw sql
engine = db.engine

import numpy as np


# In[3]:


# SEARCH is called when the magnifying glass icon is clicked with a non-empty search field.
# Parms: string = alphanumeric characters that restaurant names must begin with  
#        limit = maximum number of results to be returned
def search(string, limit): 
    
    search_json = algorithm.search(string, limit).to_json(orient ="records")
    
    
    return search_json

search('pol', 10)


# In[4]:


# FULL_LIST is called at initialization to give a full list of Phoenix restaurants and restaurant_ids to the Frontend
# Frontend code will cache the list for local search handling
# Parms: NONE! 

def full_list(): 
    
    full_list_json = algorithm.full_list().to_json(orient = "records")
    
    return full_list_json

full_list()


# ### EXPLORE MODE

# In[5]:


# USER_PROFILE is called in explore mode when a user node is clicked.
# Parms: id = id of active user node

def user_profile(user_id):
    
    # Get details for profile window   
    user_profile_df = algorithm.user_profile(user_id)
    user_profile_df['influence'] = np.round(user_profile_df['influence'],decimals = 2)
    user_profile_str_df = user_profile_df.astype(str)
    user_profile_json = user_profile_str_df.to_json(orient = "records")
    #display(user_profile_json) 
    
    # Get first/second order nodes for graph, and info for like nodes across bottom of page
    # This is for explore mode, all like nodes are LMU for active users 
    like_users_df = algorithm.like_users(user_profile_df, user_id, lmu_limit)  
    like_users = like_users_df[['user','user_id','lmu_score']].astype(str).drop_duplicates().head(10)
    like_users_json = like_users.to_json(orient= "records")
    #display(like_users_json)
    
    # Get third order nodes for graph
    recommended_restaurants_df = algorithm.recommended_restaurants(like_users_df, reco_limit)   
    #display(recommended_restaurants_df) 
    
    # Transform graph info into nodes and links lists
    user_graph_dict = algorithm.user_graph(user_id, user_profile_df, like_users_df, recommended_restaurants_df)
    links = user_graph_dict['links'].to_json(orient = 'records')
    nodes = user_graph_dict['nodes'].to_json(orient = "records")
    graph = {"links":links, "nodes":nodes}
    #display(graph)
    
    result = {"profile":user_profile_json, "graph":graph, "likes": like_users_json}
    
    return result


# RESTAURANT_PROFILE is called in explore mode when a restaurant node is clicked.
# Parms: id = id of active restaurant node

def restaurant_profile(restaurant_id):
    
    # Get details for profile window   
    restaurant_profile_df = algorithm.restaurant_profile(restaurant_id)
    restaurant_profile = restaurant_profile_df.astype(str)
    restaurant_profile_json = restaurant_profile.to_json(orient = "records")
    #display(restaurant_profile_json)
    
    # Get first/second order nodes for graph, and info for like nodes across bottom of page
    like_restaurants_df = algorithm.like_restaurants(restaurant_id, competitor_limit) 
    like_restaurants = like_restaurants_df[['restaurant','restaurant_id','compete_score']].astype(str).drop_duplicates().head(10)
    like_restaurants_json = like_restaurants.to_json(orient = "records")
    #display(like_restaurants_json)
      
    # Get third order nodes for graph   
    customer_prospects_df = algorithm.customer_prospects (like_restaurants_df, prospect_limit) 
    #display(customer_prospects_df)
      
    # Transform graph info into nodes and links lists   
    restaurant_graph_dict = algorithm.restaurant_graph (restaurant_id, restaurant_profile_df, like_restaurants_df, customer_prospects_df)    
    #display(restaurant_graph_dict) 
    links = restaurant_graph_dict['links'].to_json(orient = 'records')
    nodes = restaurant_graph_dict['nodes'].to_json(orient = "records")
    graph = {"links":links, "nodes":nodes}
    
    result = {"profile": restaurant_profile_json, "graph":graph, "likes": like_restaurants_json }
    
    return result


# ### ANALYZE MODE


# RATING_OF_RESTAURANT is called when a first-order restaurant node is clicked.
# Parms: active_user_id = id of the active user
#        restaurant _id = id of the selected first-order restaurant 

def rating_of_restaurant(active_user_id, restaurant_id,lmu_limit = 20, reco_limit = 30,competitor_limit = 20):
    
    # Get details for profile window   
    user_profile_df = algorithm.user_profile(active_user_id)
    
    # Get first/second order nodes for graph, and info for bar graph comparison 
    # This is for explore mode, all like nodes are LMU for active users 
    like_users_df = algorithm.like_users(user_profile_df, active_user_id, lmu_limit)  
    
    # Get third order nodes for graph
    recommended_restaurants_df = algorithm.recommended_restaurants(like_users_df, reco_limit)   
    #display(recommended_restaurants_df) 
    
    # Get all the restaurants name and score inforamtion to build the comparision bar graph
    user_graph_dict = algorithm.user_graph(user_id, user_profile_df, like_users_df, recommended_restaurants_df)
    nodes = user_graph_dict['nodes']
    nodes_restaurants = nodes[nodes['order']== 1][['name','score']]
    links = user_graph_dict['links'].to_json(orient = 'records')
    nodes = user_graph_dict['nodes'].to_json(orient = "records")
    graph = {"links":links, "nodes":nodes}
    comparison_json = nodes_restaurants.to_json(orient = "records")
    
    
    # Returns details of how user rated restaurant
    rating_df = algorithm.user_restaurant_rating(active_user_id,restaurant_id)
    rating = rating_df[['restaurant','user','rating','date','review','useful','funny','cool']].astype(str)
    rating_json = rating.to_json(orient = 'records')
    
    
    #return the likes nodes at the bottom
    restaurant_profile_df = algorithm.restaurant_profile(restaurant_id)   
    #Returns restaurant details with categories and attributes csv lists
    
    
    like_restaurants_df = algorithm.like_restaurants(restaurant_id, competitor_limit) 
    like_restaurants = like_restaurants_df[['restaurant','restaurant_id','compete_score']].astype(str).drop_duplicates().head(10)
    like_restaurants_json = like_restaurants.to_json(orient = "records")
    
    result = {"graph":graph, "rating":rating_json, "comparison":comparison_json,"likes":like_restaurants_json}
    return result


# RATING_BY_USER is called when a first-order user node is clicked.
# Parms:  active_restaurant_id = id of the active restaurant
#         user _id = id of the selected first-order user   

def rating_by_user(active_restaurant_id, user_id):
    
    restaurant_profile_df = algorithm.restaurant_profile (active_restaurant_id)  
   
    
    like_restaurants_df = algorithm.like_restaurants (restaurant_id, competitor_limit)  
    # Returns name and restaurant_id info to build like restaurant nodes at bottom of screen.
    # (Also provides info for bar graph in Analyze mode when a second order node is selected)
    
    customer_prospects_df = algorithm.customer_prospects (like_restaurants_df, prospect_limit) 
        
    restaurant_graph_dict = algorithm.restaurant_graph(restaurant_id, restaurant_profile_df, like_restaurants_df, customer_prospects_df)    
    # Global nodes and links dataframes are created
    nodes = restaurant_graph_dict['nodes']
    nodes_users = nodes[nodes['order']== 1][['name','score']]
    links = restaurant_graph_dict['links'].to_json(orient = 'records')
    nodes = restaurant_graph_dict['nodes'].to_json(orient = "records")
    graph = {"links":links, "nodes":nodes}
    comparison_json = nodes_users.to_json(orient = "records")
    
    rating_df = algorithm.user_restaurant_rating(user_id, active_restaurant_id)
    # Returns details of how restaurant was rated by user
    rating = rating_df[['restaurant','user','rating','date','review','useful','funny','cool']].astype(str)
    rating_json = rating.to_json(orient = 'records')    
    
    ##likes json 
    user_profile_df = algorithm.user_profile(user_id)
    # Get first/second order nodes for graph, and info for like nodes across bottom of page
    # This is for explore mode, all like nodes are LMU for active users 
    like_users_df = algorithm.like_users(user_profile_df, user_id, lmu_limit)  
    like_users = like_users_df[['user','user_id','lmu_score']].astype(str).drop_duplicates().head(10)
    like_users_json = like_users.to_json(orient= "records")
    
    
    result = {"graph": graph, "rating":rating_json, "comparison":comparison_json,"likes":like_users_json}
     
    return result



# LIKEMINDED_USER_SIMILARITY is called when a second-order user node is clicked.
# Parms: active_user_id = id of the active user
#        selected_user _id = id of the selected second-order user 

def likeminded_user_similarity (active_user_id, selected_user_id):
    
    
    ##LMU similarity table 
    active_user_profile_df = algorithm.user_profile(active_user_id)    
    
    active_like_users_df = algorithm.like_users(active_user_profile_df, active_user_id, lmu_limit) 
    # Returns information to build first and second order nodes in the graph.   
    # Also returns name and user_id information to build like user nodes at bottom of screen.
    LMU_similarity = active_like_users_df[active_like_users_df['user_id']==selected_user_id][['shared_val','shared_score','overlap_val','overlap_score','rate_sim_val','rate_sim_score','influence_val','influence_score','influ_sim_val','influ_sim_score','lmu_score']].astype(str)
    LMU_similarity_json = LMU_similarity.to_json(orient='records')
    
    ##comparision
    # Get third order nodes for graph
    recommended_restaurants_df = algorithm.recommended_restaurants(active_like_users_df, reco_limit)   
    #display(recommended_restaurants_df) 
    
    # Get all the restaurants name and score inforamtion to build the comparision bar graph
    user_graph_dict = algorithm.user_graph(active_user_id, user_profile_df, active_like_users_df, recommended_restaurants_df)
    nodes = user_graph_dict['nodes']
    nodes_restaurants = nodes[nodes['order']== 2][['name','score']]
    links = user_graph_dict['links'].to_json(orient = 'records')
    nodes = user_graph_dict['nodes'].to_json(orient = "records")
    graph = {"links":links, "nodes":nodes}
    comparison_json = nodes_restaurants.to_json(orient = "records")
    
    
    ##likes
    selected_user_profile_df = algorithm.user_profile(selected_user_id)
    # Get first/second order nodes for graph, and info for like nodes across bottom of page
    # This is for explore mode, all like nodes are LMU for active users 
    like_users_df = algorithm.like_users(selected_user_profile_df, selected_user_id, lmu_limit)  
    like_users = like_users_df[['user','user_id','lmu_score']].astype(str).drop_duplicates().head(10)
    like_users_json = like_users.to_json(orient= "records")
    
    
    result = {"graph":graph,"LMU_similarity":LMU_similarity_json,"comparison":comparison_json,"likes": like_users_json }
    
    return result


# DIRECT_COMPETITOR_SIMILARITY is called when a second-order restaurant node is clicked.
# Parms: active_restaurant_id = id of the active restaurant
#        selected_restaurant _id = id of the selected second-order restaurant 

def direct_competitor_similarity(active_restaurant_id, selected_restaurant_id):
    
    ##restaurant_similarity_json
    active_restaurant_profile_df = algorithm.restaurant_profile (active_restaurant_id)   
    # Returns restaurant details with categories and attributes csv lists
    
    active_like_restaurants_df = algorithm.like_restaurants(active_restaurant_id, competitor_limit)  
    restaurant_similarity = active_like_restaurants_df[active_like_restaurants_df['restaurant_id']==selected_restaurant_id][['shared_val','shared_score','overlap_val','overlap_score','rate_sim_val','rate_sim_score','zip_val','zip_score','compete_score']].astype(str)
    restaurant_similarity_json = restaurant_similarity.to_json(orient='records') 
    
    ##comparsion
    customer_prospects_df = algorithm.customer_prospects(active_like_restaurants_df, prospect_limit) 
        
    restaurant_graph_dict = algorithm.restaurant_graph(active_restaurant_id, active_restaurant_profile_df, active_like_restaurants_df, customer_prospects_df)    
    # Global nodes and links dataframes are created
    nodes = restaurant_graph_dict['nodes']
    nodes_users = nodes[nodes['order']== 2][['name','score']]
    links = restaurant_graph_dict['links'].to_json(orient = 'records')
    nodes = restaurant_graph_dict['nodes'].to_json(orient = "records")
    graph = {"links":links, "nodes":nodes}
    comparison_json = nodes_users.to_json(orient = "records")
    
    ##likes 
    restaurant_profile_df = algorithm.restaurant_profile(selected_restaurant_id)   
    
    like_restaurants_df = algorithm.like_restaurants(selected_restaurant_id, competitor_limit) 
    like_restaurants = like_restaurants_df[['restaurant','restaurant_id','compete_score']].astype(str).drop_duplicates().head(10)
    like_restaurants_json = like_restaurants.to_json(orient = "records")
    
    
    result = {"graph":graph,"restaurant_similarity":restaurant_similarity_json,"comparison":comparison_json,"likes": like_restaurants_json }

    
    return result


# RECOMMENDED_RESTAURANT_RELEVANCE is called when a third-order restaurant node is clicked.
# Parms: active_user_id = id of the active user
#        selected_restaurant _id = id of the selected third-order restaurant

def recommended_restaurant_relevance(active_user_id, selected_restaurant_id):
    
    active_user_profile_df = algorithm.user_profile(active_user_id)            
    active_like_users_df = algorithm.like_users (active_user_profile_df, active_user_id, lmu_limit) 
    recommended_restaurants_df = algorithm.recommended_restaurants (active_like_users_df, reco_limit)   
    user_graph_dict = algorithm.user_graph(active_user_id, active_user_profile_df, active_like_users_df, recommended_restaurants_df)    
    
    ##graph 
    links = user_graph_dict['links'].to_json(orient = 'records')
    nodes = user_graph_dict['nodes'].to_json(orient = "records")
    graph = {"links":links, "nodes":nodes}
    
    ##relevance 
    reco_restaurant_relevance = recommended_restaurants_df[recommended_restaurants_df['restaurant_id']==selected_restaurant_id]
    relevance_df = reco_restaurant_relevance[['user','lmu_rating','lmu_score','contribution','relevancy']]
    if (reco_restaurant_relevance.shape[0] == 1):
        avg_rating = reco_restaurant_relevance['avg_rating'].values[0]
        restaurant_similarity = 5.0
        restaurant_contribution = avg_rating * restaurant_similarity
        restaurant_relevancy = reco_restaurant_relevance['relevancy'].values[0]
        
        restaurant_df = pd.DataFrame({'user':["Restaurant's Average Rating"],
                                       "lmu_rating":[avg_rating],
                                       "lmu_score":[restaurant_similarity],
                                       "contribution":[restaurant_contribution],
                                        "relevancy":[restaurant_relevancy]})
           
        relevance_df = pd.concat([relevance_df,restaurant_df],axis = 0)
    
    relevance = relevance_df.astype(str)
    relevance_json = relevance.to_json(orient = 'records')
            
    ##comparison 
    nodes = user_graph_dict['nodes']
    nodes_users = nodes[nodes['order']== 3][['name','score']]
    comparison_json = nodes_users.to_json(orient = "records")
        
    ##likes 
    selected_restaurant_profile_df = algorithm.restaurant_profile(selected_restaurant_id)   
    selected_like_restaurants_df = algorithm.like_restaurants(selected_restaurant_id, competitor_limit)  
    like_restaurants = selected_like_restaurants_df[['restaurant','restaurant_id','compete_score']].astype(str).drop_duplicates().head(10)
    like_restaurants_json =like_restaurants.to_json(orient = "records")
    
    result = {"graph":graph,"relevance":relevance_json,"comparison":comparison_json, "likes":like_restaurants_json }
    
    return result


# CUSTOMER_PROSPECT_RELEVANCE is called when a third-order user node is clicked.
# Parms: active_restaurant_id = id of the active restaurant
#        user _id = id of the selected third-order user 

def customer_prospect_relevance(active_restaurant_id, selected_user_id):
    
    ##pre-calcualtion
    active_restaurant_profile_df = algorithm.restaurant_profile(active_restaurant_id)   
    active_like_restaurants_df = algorithm.like_restaurants (active_restaurant_id, competitor_limit) 
    customer_prospects_df = algorithm.customer_prospects (like_restaurants_df, prospect_limit) 
    restaurant_graph_dict = algorithm.restaurant_graph (restaurant_id, restaurant_profile_df, like_restaurants_df, customer_prospects_df)    

    ##graph
    links = restaurant_graph_dict['links'].to_json(orient = 'records')
    nodes = restaurant_graph_dict['nodes'].to_json(orient = "records")
    graph = {"links":links, "nodes":nodes}
    
    
    ##relevance
    customer_prospect_relevance = customer_prospects_df[customer_prospects_df['user_id']==selected_user_id]
    relevance_df = customer_prospect_relevance[['restaurant','user_rating','compete_score','contribution','relevancy']]
    if (customer_prospect_relevance.shape[0] == 1):
        avg_rating = customer_prospect_relevance['avg_rating'].values[0]
        user_similarity = 5.0
        user_contribution = avg_rating * user_similarity
        user_relevancy = customer_prospect_relevance['relevancy'].values[0]
        
        user_df = pd.DataFrame({'restaurant':["User's Average Rating"],
                                       "user_rating":[avg_rating],
                                       "compete_score":[user_similarity],
                                       "contribution":[user_contribution],
                                        "relevancy":[user_relevancy]})
           
        relevance_df = pd.concat([relevance_df,user_df],axis = 0)
        
    relevance = relevance_df.astype(str)
    relevance_json = relevance.to_json(orient = 'records')
       
    
    ##comparison
    nodes = restaurant_graph_dict['nodes']
    nodes_restaurants = nodes[nodes['order']== 3][['name','score']]
    comparison_json = nodes_restaurants.to_json(orient = "records")
    
    
    ##likes 
    selected_user_profile_df = algorithm.user_profile(selected_user_id)        
    selected_like_users_df = algorithm.like_users(selected_user_profile_df, selected_user_id, lmu_limit)   
    like_users = selected_like_users_df[['user','user_id','lmu_score']].astype(str).drop_duplicates().head(10)
    like_users_json =like_users.to_json(orient = "records")
    
    
    result = {"graph":graph,"relevance":relevance_json,"comparison":comparison_json, "likes":like_users_json}
    return result

# #### Note: In the following two API calls, if frontend can preserve the graph, then active_id and active_ type are not required (in this case, graph info will not be returned):



# USER_SIMILARITY is called when a user node has been selected and a “like node” is clicked.
# Parms:  active_id = id of the active node
#         active_type = ‘user’ or ‘restaurant’
#         selected_user _id = id of the selected user node
#         like_user_id = id of the like user node 

def user_similarity(selected_user_id, like_user_id):
    
    selected_user_profile_df = user_profile(selected_user_id)       
    
    selected_like_users_df = algorithm.like_users(selected_user_profile_df, selected_user_id, lmu_limit)
    
    user_similarity = selected_like_users_df[selected_like_users_df['user_id']==like_user_id]
  
    
    user_similarity_df = user_similarity[['shared_val','shared_score','overlap_val','overlap_score',
                                         'rate_sim_val','rate_sim_score','influence_val','influence_score',
                                         'influ_sim_val','influ_sim_score','lmu_score']].drop_duplicates().astype(str)
    
    user_similarity_json = user_similarity_df.to_json(orient = "records")
    
    
    
    return user_similarity_json


# RESTAURANT_SIMILARITY is called when a restaurant node has been selected and a “like node” is clicked.
# Parms: active_id = id of the active node
#        active_type = ‘user’ or ‘restaurant’
#        selected_restaurant _id = id of the selected user node
#        like_restaurant_id = id of the like user node

def restaurant_similarity(selected_restaurant_id, like_restaurant_id, competitor_limit = 20):
    
    selected_restaurant_profile_df = algorithm.restaurant_profile (selected_restaurant_id)   
   
    selected_like_restaurants_df = algorithm.like_restaurants (selected_restaurant_id, competitor_limit)  
    
    restaurant_similarity = selected_like_restaurants_df[selected_like_restaurants_df['restaurant_id']==like_restaurant_id]
  
    
    restaurant_similarity_df = restaurant_similarity[['shared_val','shared_score','overlap_val','overlap_score',
                                         'review_sim_val','review_sim_score','rate_sim_val','rate_sim_score',
                                         'zip_val','zip_score','compete_score']].drop_duplicates().astype(str)
    
    restaurant_similarity_json = restaurant_similarity_df.to_json(orient = "records")
    
    
    return restaurant_similarity_json
