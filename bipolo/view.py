# -*- coding: utf-8 -*-
import json
from flask import render_template, request, jsonify

from bipolo import app, db, api

# Engine is the key to executing raw sql
engine = db.engine


@app.route('/')
def index():
    return render_template('user_dashboard.html')

@app.route('/json_demo')
def json_demo():
    return render_template('json_demo.html')



# ***********Setup Global Variables************
limit = 10
lmu_limit=20
reco_limit=30
competitor_limit = 20
prospect_limit = 30
# **********  SEARCH MODE ROUTINES  **********


# SEARCH is called when the magnifying glass icon is clicked with a non-empty search field.
# Parms: string = alphanumeric characters that restaurant names must begin with

@app.route('/search')
def search():
    string = request.args.get('string', '')

    results = api.search(string,limit)
    return results.rename(columns={'name': 'text'}).to_json(orient='records')


# FULL_LIST is called at initialization to give a full list of Phoenix restaurants and restaurant_ids to the Frontend
# Frontend code will cache the list for local search handling
# Parms: NONE!

@app.route('/full_list/')
def full_list():

    results = api.full_list()
    results_dict = json.loads(results.to_json(orient='records'))

    adict = {
        'results': results_dict
        }

    return jsonify(adict)


# **********  EXPLORE MODE ROUTINES  **********


# USER_PROFILE is called in explore mode when a user node is clicked.
# Parms: user_id = id of active user node

@app.route('/user_profile/<user_id>')
def user_profile(user_id):

    profile, graph_dict, like = api.user_profile(user_id)
    profile_dict = json.loads(profile.to_json(orient='records'))
    nodes_dict = json.loads(graph_dict['nodes'].to_json(orient='records'))
    links_dict = json.loads(graph_dict['links'].to_json(orient='records'))
    like_dict = json.loads(like.to_json(orient='records'))

    adict = {
        'profile': profile_dict,
        'nodes': nodes_dict,
        'links': links_dict,
        'like': like_dict
    }
    return jsonify(adict)


# RESTAURANT_PROFILE is called in explore mode when a restaurant node is clicked.
# Parms: restaurant_id = id of active restaurant node

@app.route('/restaurant_profile/<restaurant_id>')
def restaurant_profile(restaurant_id):

    profile, graph_dict, like = api.restaurant_profile(restaurant_id)
    profile_dict = json.loads(profile.to_json(orient='records'))
    nodes_dict = json.loads(graph_dict['nodes'].to_json(orient='records'))
    links_dict = json.loads(graph_dict['links'].to_json(orient='records'))
    like_dict = json.loads(like.to_json(orient='records'))

    adict = {
        'profile': profile_dict,
        'nodes': nodes_dict,
        'links': links_dict,
        'like': like_dict
    }

    return jsonify(adict)


# **********  ANALYSIS MODE ROUTINES  **********


# RATING_OF_RESTAURANT is called when a first-order restaurant node is clicked.
# Parms: active_user_id = id of the active user
#        restaurant _id = id of the selected first-order restaurant
@app.route('/rating_of_restaurant')
def rating_of_restaurant():
    active_user_id = request.args.get('active_user_id')
    restaurant_id  = request.args.get('restaurant_id')

    # You want nodes, links, like, rating, comparison
    rating, comparison, like = api.rating_of_restaurant(active_user_id, restaurant_id)
    #profile_dict = json.loads(profile.to_json(orient = 'records'))
    #nodes_dict = json.loads(graph_dict['nodes'].to_json(orient='records'))
    rating_dict = json.loads(rating.to_json(orient = "records"))
    #links_dict = json.loads(graph_dict['links'].to_json(orient='records'))
    like_dict = json.loads(like.to_json(orient='records'))
    comparison_dict = json.loads(comparison.to_json(orient = "records"))

    adict = {
        #"profile": profile_dict,
        #"nodes":nodes_dict,
        #"links":links_dict,
        "like":like_dict,
        "rating": rating_dict,
        "comparison": comparison_dict
        }

    return jsonify(adict)

# RATING_BY_USER is called when a first-order user node is clicked.
# Parms:  active_restaurant_id = id of the active restaurant
#         user _id = id of the selected first-order user

@app.route ('/rating_by_user')
def rating_by_user():
    active_restaurant_id = request.args.get('active_restaurant_id')
    user_id = request.args.get('user_id')
                                                      # You want nodes, links, like, rating, comparison
    rating, comparison, like = api.rating_by_user(active_restaurant_id, user_id)
    #profile_dict = json.loads(profile.to_json(orient = 'records'))
    #nodes_dict = json.loads(graph_dict['nodes'].to_json(orient='records'))
    #links_dict = json.loads(graph_dict['links'].to_json(orient='records'))
    rating_dict = json.loads(rating.to_json(orient="records"))
    like_dict = json.loads(like.to_json(orient='records'))
    comparison_dict = json.loads(comparison.to_json(orient = "records"))

    adict = {
        #"profile": profile_dict,
        #"nodes": nodes_dict,
        #"links": links_dict,
        "like": like_dict,
        "rating": rating_dict,
        "comparison": comparison_dict
        }

    return jsonify(adict)


# LIKEMINDED_USER_SIMILARITY is called when a second-order user node is clicked.
# Parms: active_user_id = id of the active user
#        selected_user _id = id of the selected second-order user

@app.route ('/likeminded_user_similarity')
def likeminded_user_similarity():
    active_user_id = request.args.get('active_user_id')
    selected_user_id = request.args.get('selected_user_id')

                              # Order by nodes, links, like, lmu_similarity, comparison
    LMU_similarity, comparison, like = api.likeminded_user_similarity(active_user_id, selected_user_id)
    #profile_dict = json.loads(profile.to_json(orient = 'records'))
    #nodes_dict = json.loads(graph_dict['nodes'].to_json(orient='records'))
    #links_dict = json.loads(graph_dict['links'].to_json(orient='records'))
    like_dict = json.loads(like.to_json(orient='records'))
    comparison_dict = json.loads(comparison.to_json(orient="records"))
    LMU_similarity_dict = json.loads(LMU_similarity.to_json(orient = "records"))   

    adict = {
        #"profile": profile_dict,
        #'nodes': nodes_dict,
        #"links": links_dict,
        "like": like_dict,
        "LMU_similarity":LMU_similarity_dict,
        "comparison": comparison_dict
        }

    return jsonify(adict)

# DIRECT_COMPETITOR_SIMILARITY is called when a second-order restaurant node is clicked.
# Parms: active_restaurant_id = id of the active restaurant
#        selected_restaurant _id = id of the selected second-order restaurant

@app.route ('/direct_competitor_similarity')
def direct_competitor_similarity():
    active_restaurant_id = request.args.get('active_restaurant_id')
    selected_restaurant_id = request.args.get('selected_restaurant_id')

                                  # Order by nodes, links, like, direct_competitor_similarity, comparison
    direct_competitor_similarity, comparison, like = api.direct_competitor_similarity(active_restaurant_id, selected_restaurant_id)
    #profile_dict = json.loads(profile.to_json(orient = 'records'))
    #nodes_dict = json.loads(graph_dict['nodes'].to_json(orient='records'))
    #links_dict = json.loads(graph_dict['links'].to_json(orient='records'))
    like_dict = json.loads(like.to_json(orient='records'))
    comparison_dict = json.loads(comparison.to_json(orient="records"))
    direct_competitor_similarity_dict = json.loads(direct_competitor_similarity.to_json(orient="records"))

    adict = {
        #"profile": profile_dict,
        #'nodes': nodes_dict,
        #"links": links_dict,
        "like": like_dict,
        "comparison": comparison_dict,
        "direct_competitor_similarity": direct_competitor_similarity_dict
            }

    return jsonify(adict)

# RECOMMENDED_RESTAURANT_RELEVANCE is called when a third-order restaurant node is clicked.
# Parms: active_user_id = id of the active user
#        selected_restaurant _id = id of the selected third-order restaurant

@app.route ('/recommended_restaurant_relevance')
def recommended_restaurant_relevance():
    active_user_id = request.args.get('active_user_id')
    selected_restaurant_id = request.args.get('selected_restaurant_id')

                                 # Order by nodes, links, like, relevance, comparison
    recommended_restaurant_relevance, comparison, like = api.recommended_restaurant_relevance(active_user_id, selected_restaurant_id)
    #profile_dict = json.loads(profile.to_json(orient = 'records'))
    #nodes_dict = json.loads(graph_dict['nodes'].to_json(orient='records'))
    #links_dict = json.loads(graph_dict['links'].to_json(orient='records'))
    like_dict = json.loads(like.to_json(orient='records'))
    comparison_dict = json.loads(comparison.to_json(orient="records"))
    recommended_restaurant_relevance_dict = json.loads(recommended_restaurant_relevance.to_json(orient="records"))

    adict = {
        #"profile": profile_dict,
        #"nodes": nodes_dict,
        #"links": links_dict,
        "like": like_dict,
        "comparison": comparison_dict,
        "recommended_restaurant_relevance": recommended_restaurant_relevance_dict
        }

    return jsonify(adict)

# CUSTOMER_PROSPECT_RELEVANCE is called when a third-order user node is clicked.
# Parms: active_restaurant_id = id of the active restaurant
#        selected_user _id = id of the selected third-order user
@app.route ('/customer_prospect_relevance')
def customer_prospect_relevance():
    active_restaurant_id = request.args.get('active_restaurant_id')
    selected_user_id = request.args.get('selected_user_id')

                                           # Order by nodes, links, like, relevance, comparison
    customer_prospect_relevance, comparison, like = api. customer_prospect_relevance(active_restaurant_id, selected_user_id)
    #profile_dict = json.loads(profile.to_json(orient = 'records'))
    #nodes_dict = json.loads(graph_dict['nodes'].to_json(orient='records'))
    #links_dict = json.loads(graph_dict['links'].to_json(orient='records'))
    like_dict = json.loads(like.to_json(orient='records'))
    comparison_dict = json.loads(comparison.to_json(orient="records"))
    customer_prospect_relevance_dict = json.loads(customer_prospect_relevance.to_json(orient="records"))

    adict = {
        #"profile": profile_dict,
        #"nodes": nodes_dict,
        #"links": links_dict,
        "like": like_dict,
        "comparison": comparison_dict,
        "customer_prospect_relevance": customer_prospect_relevance_dict
    }

    return jsonify(adict)

# USER_SIMILARITY is called when a user node has been selected and a “like node” is clicked.
# Parms:  selected_user _id = id of the selected user node
#         like_user_id = id of the like user node
@app.route ('/user_similarity')                           ## In here, either active user or active restaurant?
def user_similarity():
    selected_user_id = request.args.get('selected_user_id')
    like_user_id = request.args.get('like_user_id')

    user_similarity = api.user_similarity(selected_user_id, like_user_id)
    user_similarity_adict = json.loads(user_similarity.to_json(orient='records'))

    adict = {'user_similarity': user_similarity_adict}

    return jsonify(adict)

# RESTAURANT_SIMILARITY is called when a restaurant node has been selected and a “like node” is clicked.
# Parms: selected_restaurant _id = id of the selected user node
#        like_restaurant_id = id of the like user node

@app.route ('/restaurant_similarity')                        ## In here, either active user or active restaurant?
def restaurant_similarity():
    selected_restaurant_id = request.args.get('selected_restaurant_id')
    like_restaurant_id = request.args.get('like_restaurant_id')

    restaurant_similarity = api.restaurant_similarity(selected_restaurant_id, like_restaurant_id)
    restaurant_similarity_adict = json.loads(restaurant_similarity.to_json(orient='records'))

    adict = {'restaurant_similarity': restaurant_similarity_adict}

    return jsonify(adict)