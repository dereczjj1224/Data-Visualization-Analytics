/*
 * Direct implementation of the service api methods available.
 */
function Controller() {
    this.cache = new WeakMap();
    this.active_id = 0;
	this.active_name = '';
	this.active_type = null;
	this.selected_id = 0;
	this.selected_name = '';
	this.selected_type = null;

    this.show_modal = function() {
        document.getElementById("data-is-loading").showModal();
    }

    this.hide_modal = function() {
        document.getElementById("data-is-loading").close();
    }

    this.try_cache_or_retrieve = function(key, url, callback) {
        if (this.cache.has(key)) {
            //console.log(url+": from cache");
            callback(this.cache.get(key));
        }  else {
            //console.log(url+" : requesting");
            this.show_modal();
            var resp = $.ajax({
                url: url,
                dataType: 'json',
                success: function(d) {
                    //console.log(key);
                    controller.cache.set(key, d);
                    callback(d);
                }
            });
        }
    }

	this.update_status_note = function(txtData) {
		//Update the graph title / information / status note
        if (true) {
            var txt = txtData[0]['text'];
            txt += '.  Click to ANALYZE. Double-click to EXPLORE.';
            d3.select(".explain").text(txt);
            return;
        }
        /*
		txtData.forEach (function(d, i) {
			
			txtStatus = svgGraph.selectAll("." + d.css)
			txtStatus.selectAll("*")
				.data([{}])
				.exit().remove();
			
			txtStatus
				.data([d])
				.enter()
				.append("text")
				.merge(txtStatus) 
				.attr("class", d.css)
				.attr("textAnchor", "middle")
				.attr("x", -350)
				.attr("y", i*30-320)
				.text(d.text);
						
		});
		*/
	}
	
	this.update_barchart_title = function(txtData) {
        d3.select("#score-comparison-container-h3").text(txtData[0]['text']);
	}
	
	this.show_graph_legend = function() {
		svgLegend.selectAll("g").remove();
				
		data_Uroot = [{"name":"User Root", "css":"user-circle0"},
			{"name":"Reviewed Restaurant", "css":"restaurant-circle1"},
			{"name":"Like-Minded User", "css":"user-circle2"},
			{"name":"Recommended Restaurant", "css":"restaurant-circle3"}];
			
		data_Rroot = [{"name":"Restaurant Root", "css":"restaurant-circle0"},
			{"name":"Reviewing User", "css":"user-circle1"},
			{"name":"Direct Competitor", "css":"restaurant-circle2"},
			{"name":"Customer Prospect", "css":"user-circle3"}];
		
		data = (controller.active_type == 'R') ? data_Rroot : data_Uroot
		//console.log(data);
		
		svgLeg = svgLegend.selectAll("g")
			.data(data)
			.enter()
			.append("g")
			.attr("class", "legendNode");
			
		svgLeg.append("circle")
			.attr("r", 15)
			.attr("cx", function (d, i) {
				return i * 800 /4 + 100;
			})
			.attr("cy", 20)
			.attr("class", function (d) {
				return d.css;
			});
				
		svgLeg.append("text")
			.attr("class", "legendText")
			.attr("x", function (d, i) {
				return i * 800 /4 + 100 + 20;
			})
			.attr("y", 23)
			.text(function (d) {
				return d.name
			});
	}

	this.show_graph_selected = function(d) {
		// format the selected graph node to stand out from the rest
		// highlight links from selected to active node
		// if in analyze mode, call right sidebar table and barchart updates
		//console.log(d);
		
		controller.selected_type = (d.type == 'user') ? 'U' : 'R';
		d3.selectAll(".selected-circle").classed("selected-circle", false);
		var gnodes = svgGraph.selectAll("g");
		var id = ''
		gnodes.each(function(n) {
			if (n.type == 'restaurant') { id = n.restaurant_id 
			} else if (n.type == 'user') { id = n.user_id }
			if (n.id == d.id) {
				d3.select(this).classed("selected-circle", true);
				controller.selected_id = d.id;
			}
		});
		color_links_to_active_node(d);
		controller.set_node_as_selected(d);
	}

    this.handle_restaurant_as_root_result = function(data) {
        var profile = data['profile'][0],
            nodes = data['nodes'],
            links = data['links'],
            like = data['like'];
        render_rest_profile(profile);
        render_graph(nodes, links);
		controller.active_name = profile.name
		controller.update_status_note([
			{"text":"Graph loaded for " + controller.active_name, "css":"graph-title"},
			{"text":"Single click a node to analyze", "css":"graph-instruction1"}, 
			{"text":"Double click a node to explore", "css":"graph-instruction2"}])
        controller.show_graph_legend();
		controller.hide_modal();
    }
	
    this.handle_user_as_root_result = function(data) {
        var profile = data['profile'][0],
            nodes = data['nodes'],
            links = data['links'],
            like = data['like'];
        render_user_profile(profile);
        render_graph(nodes, links);
		controller.active_name = profile.name
		controller.update_status_note([
			{"text":"A new graph was loaded for " + controller.active_name, "css":"graph-title"},
			{"text":"Single click a node to analyze", "css":"graph-instruction1"}, 
			{"text":"Double click a node to explore", "css":"graph-instruction2"}])
		controller.show_graph_legend();
        controller.hide_modal();
    }
	
    this.set_restaurant_as_root = function(id) {
        //console.log("set rest as root " + id);
        this.active_id = id;
        this.active_type = 'R';
        var url = '/restaurant_profile/' + id;
		clear_comparison_table();
		clear_bar_chart();
        this.try_cache_or_retrieve({url: url}, url, this.handle_restaurant_as_root_result);
    }

    this.set_user_as_root = function(id) {
        this.active_id = id;
        this.active_type = 'U';
        var url = '/user_profile/' + id;
		clear_comparison_table();
		clear_bar_chart();
        this.try_cache_or_retrieve({url: url}, url, this.handle_user_as_root_result);
    }

    this.handle_user_level_1 = function(d) {
        //console.log(d);
        clear_relevance_table();
        clear_comparison_table();
		clear_bar_chart();
        render_rating_table(d['rating'][0], 'U', 1);
		render_bar_chart(d['comparison'], controller.selected_type)
		controller.update_barchart_title([{"text":"User Rating Comparison", "css":"barChartTitle"}]);
        controller.hide_modal();
    }

    this.handle_user_level_2 = function(d) {
        //console.log(d);
        clear_relevance_table();
        clear_comparison_table();
		clear_bar_chart();
        render_similarity_table(d['LMU_similarity'][0], 'U');
		render_bar_chart(d['comparison'], controller.selected_type)
		controller.update_barchart_title([{"text":"User Similarity Comparison", "css":"barChartTitle"}]);
        controller.hide_modal();
    }

    this.handle_user_level_3 = function(d) {
        console.log(d);
        clear_relevance_table();
        clear_comparison_table();
		clear_bar_chart();
        render_comparison_table(d['recommended_restaurant_relevance'], 'U');
		render_bar_chart(d['comparison'], controller.selected_type)
		controller.update_barchart_title([{"text":"Recommended Restaurant Comparison", "css":"barChartTitle"}]);
        controller.hide_modal();
    }

    this.handle_restaurant_level_1 = function(d) {
		//console.log(d);
        clear_relevance_table();
        clear_comparison_table();
		clear_bar_chart();
        render_rating_table(d['rating'][0], 'R', 1);
		render_bar_chart(d['comparison'], controller.selected_type)
		controller.update_barchart_title([{"text":"User Rating Comparison", "css":"barChartTitle"}]);
        controller.hide_modal();
    }

    this.handle_restaurant_level_2 = function(d) {
        //console.log(d);
        clear_relevance_table();
        clear_comparison_table();
		clear_bar_chart();
        render_similarity_table(d['direct_competitor_similarity'][0], 'R');
		render_bar_chart(d['comparison'], controller.selected_type)
		controller.update_barchart_title([{"text":"Competitor Similarity Comparison", "css":"barChartTitle"}]);
        controller.hide_modal();
    }

    this.handle_restaurant_level_3 = function(d) {
        console.log(d);
        clear_relevance_table();
        clear_comparison_table();
		clear_bar_chart();
        render_comparison_table(d['customer_prospect_relevance'], 'R');
		render_bar_chart(d['comparison'], controller.selected_type)
		controller.update_barchart_title([{"text":"Customer Prospect Comparison", "css":"barChartTitle"}]);
        controller.hide_modal();
    }

    this.set_node_as_selected = function(d) {
		//console.log(d)
		controller.selected_id = d.id
		controller.selected_name = d.name
		controller.selected_type = (d.type == 'user')? 'U':'R'
		
        var order = d.order,
            url = null,
            callback = null;
		if (this.active_type == "R") {
			// active node type is restaurant
			if (order == 1) {
				url = '/rating_by_user?active_restaurant_id=' + this.active_id + '&user_id=' + d.id;
				callback = this.handle_restaurant_level_1;
			} else if (order == 2) {
				url = '/direct_competitor_similarity?active_restaurant_id=' + this.active_id + '&selected_restaurant_id=' + d.id;
				callback = this.handle_restaurant_level_2;
			} else if (order == 3) {
				url = '/customer_prospect_relevance?active_restaurant_id=' + this.active_id + '&selected_user_id=' + d.id;
				callback = this.handle_restaurant_level_3;
			}
		} else {
			// active node type is user
			if (order == 1) {
				url = '/rating_of_restaurant?active_user_id=' + this.active_id + '&restaurant_id=' + d.id;
				callback = this.handle_user_level_1;
			} else if (order == 2) {
				url = '/likeminded_user_similarity?active_user_id=' + this.active_id + '&selected_user_id=' + d.id;
				callback = this.handle_user_level_2;
			} else if (order == 3) {
				url = '/recommended_restaurant_relevance?active_user_id=' + this.active_id + '&selected_restaurant_id=' + d.id;
				callback = this.handle_user_level_3;
			}
		}
		controller.update_status_note([
			{"text":"Right panels show relationships between " + controller.selected_name + " and " + controller.active_name, "css":"graph-title"},
			{"text":"Single click a node to analyze", "css":"graph-instruction1"}, 
			{"text":"Double click a node to explore", "css":"graph-instruction2"}])
        //console.log(d);
        //console.log(url);
        if (order !=0) {
			this.try_cache_or_retrieve({url:url}, url, callback)
			controller.update_status_note([
			{"text":"Right panels show relationships between " + controller.selected_name + " and " + controller.active_name, "css":"graph-title"},
			{"text":"Single click a node to analyze", "css":"graph-instruction1"}, 
			{"text":"Double click a node to explore", "css":"graph-instruction2"}]);
		} else {
			clear_relevance_table();
			//clear_comparison_table();
			clear_bar_chart();
		}
    }
}

controller = new Controller();

/***
 * Search Bar - register necessary event listeners
 */
$(document).ready(function () {
    $('#search-box').select2({
        minimumInputLength: 1,
        ajax: {
            url: '/search',
            dataType: 'json',
            data: function (params) {
                return {
                    string: params.term,
                    limit: 20
                };
            },
            processResults: function (data) {
                return {
                    'results': data
                }
            }
        }
    });

    /***
     * React to the search selected event
     */
    $('.search-box').on('select2:select', function (e) {
        //console.log('selected ' + e.params.data.id);
        controller.set_restaurant_as_root(e.params.data.id);
		document.getElementById("search-box").options.length = 0;
    });

});


function render_user_profile(profile) {
    var tag = d3.select(".active-node-container");
	tag.selectAll("*").remove();

	//d3.select("#active-node-container-h3").text("User Profile");

	// Add the table
    var tbl = tag.append("table");
    tbl.attr("id", "active-node-tbl").attr("style", "width:100%");
    tbl.classed('active-node-tbl', true)
    var tr;
	
	var hdr = 'User Profile';
	d3.select("#active-node-container-h3").text(hdr);

    var data_to_show = {
        'Name': profile.name,
        'Total Reviews': profile.total_reviews,
        'Avg Rating': profile.avg_rating,
        'Yelping Since': profile.yelping_since,
        'Influence': profile.influence
    }

    Object.keys(data_to_show).forEach(function (key) {
        var val1 = data_to_show[key];

        tr = tbl.append('tr');
        if (key == "Yelping Since") {
            var t = new Date(1970, 0, 1); // Epoch
            t.setSeconds(parseInt(val1) / 1000);
            console.log(t);
            val1 = t.toLocaleDateString('en-US');
        }

        tr.append('td').html(key);
        tr.append('td').html(val1);
    });
}

function render_rest_profile(rest) {
    var tag = d3.select(".active-node-container");
    tag.selectAll("*").remove();
    
	// Add the title
    //d3.select("#active-node-container-h3").text("Restaurant Profile");

	// Add the table
    var tbl = tag.append("table");
    tbl.attr("id", "active-node-tbl").attr("style", "width:100%");
    tbl.classed('active-node-tbl', true);
    var tr;
	
	var hdr = 'Restaurant Profile';
	d3.select("#active-node-container-h3").text(hdr);

    var data_to_show = {
        'Name': rest.name,
        'Avg Rating': rest.avg_rating,
        'Total Reviews': rest.total_reviews,
        'Neighborhood': rest.neighborhood,
        "Address": rest.address,
        "City": rest.city,
        "State, Zip": rest.state + ", " + rest.zip
    }

    Object.keys(data_to_show).forEach(function (key) {
        tr = tbl.append('tr');
        tr.append('td').html(key);
        tr.append('td').html(data_to_show[key]);
    });
}

function clear_relevance_table() {
    d3.select("#similarity-container-h3").html("&nbsp;");
    var tag = d3.select(".similarity-container");
    tag.selectAll("table").remove();
}

function render_rating_table(json, type, level) {
    var tag = d3.select(".similarity-container");
    tag.selectAll("table").remove();
    var tbl = tag.append("table");
    tbl.attr("id", "similarity_tbl").attr("style", "width:100%;");
    tbl.classed('display', true).classed('compact', true);
    var tr;

	var hdr = type == 'R' ? 'Rating by User': 'Rating of Restaurant';
    d3.select("#similarity-container-h3").text(hdr);

    tr = tbl.append("thead").append("tr");
    tr.append("th").html("Name");
    tr.append("th").html("Value");
	
	//limit review length
	var maxLen = 300
	json['review'] = json['review'].slice(0,maxLen)

    var data_to_show = {
        'Restaurant': ['restaurant'],
        'User': ['user'],
        "Rating": ['rating'],
        "Date": ['date'],
        "Review": ['review'],
        "Review Useful": ['useful'],
        "Voted Funny": ['funny'],
        'Voted Cool': ['cool'],
    }

    tbl = tbl.append('tbody'); // being a little lazy here
    Object.keys(data_to_show).forEach(function (key) {
        tr = tbl.append('tr');
        tr.append('td').html(key);
        var key1=data_to_show[key][0];
        var val1= json[key1];
        if (key == "Date") {
            var t = new Date(1970, 0, 1); // Epoch
            t.setSeconds(parseInt(val1) / 1000);
            console.log(t);
            val1 = t.toLocaleDateString('en-US');
        } else if (key == 'Rating') {
            var txt = "";
            for (i=0; i < Math.floor(val1); i++) {
                txt += '<i class="fas fa-star"></i>';
            }
            if (val1.toString().endsWith('.5')) {
                txt += '<i class="fas fa-star-half"></i>';
            }
            val1 = txt;
        }

        tr.append('td').html(val1);
    });
}

function render_similarity_table(json, type) {
    var tag = d3.select(".similarity-container");
    tag.selectAll("table").remove();
    var tbl = tag.append("table");
    tbl.attr("id", "similarity_tbl").attr("style", "width:100%;");
    tbl.classed('display', true).classed('compact', true);
    var tr;

    tr = tbl.append("thead").append("tr");
    tr.append("th").html("Factor");
    tr.append("th").classed("metric",true).html("Value");
    tr.append("th").classed("metric", true).html("Score");
	
    var hdr = type == 'R' ? 'Direct Competitor Similarity': 'User Similarity';
	d3.select("#similarity-container-h3").text(hdr);
	
	var numDigits = 2

    tbl = tbl.append('tbody');
    if (type == 'U') {
        tr = tbl.append('tr');
        tr.append('td').html('Shared Reviews');
        tr.append('td').classed("metric", true).html(json['shared_val']);
        tr.append('td').classed("metric", true).html(Number(json['shared_score']).toFixed(numDigits));

        tr = tbl.append('tr');
        tr.append('td').html('Reviewed Restaurant Overlap');
        tr.append('td').classed("metric", true).html(json['overlap_val']);
        tr.append('td').classed("metric", true).html(Number(json['overlap_score']).toFixed(numDigits));

        tr = tbl.append('tr');
        tr.append('td').html("Restaurant Ratings Similarity");
        tr.append('td').classed("metric", true).html(json['rate_sim_val']);
        tr.append('td').classed("metric", true).html(Number(json['rate_sim_score']).toFixed(numDigits));

        tr = tbl.append('tr');
        tr.append("td").html("User Influence Index");
        tr.append('td').classed("metric", true).html(json['influence_val']);
        tr.append('td').classed("metric", true).html(Number(json['influence_score']).toFixed(numDigits));

        tr = tbl.append('tr');
        tr.append("td").html("Influence Index Similarty");
        tr.append('td').classed("metric", true).html(json['influ_sim_val']);
        tr.append('td').classed("metric", true).html(Number(json['influ_sim_score']).toFixed(numDigits));

        tr = tbl.append('tr');
        tr.append("td").html("Total");
        tr.append("td").html("");
        tr.append("td").classed("metric", true).html(Number(json['lmu_score']).toFixed(numDigits));
    } else {
        tr = tbl.append('tr');
        tr.append('td').html('Shared Customers');
        tr.append('td').classed("metric", true).html(json['shared_val']);
        tr.append('td').classed("metric", true).html(Number(json['shared_score']).toFixed(numDigits));

        tr = tbl.append('tr');
        tr.append('td').html('Customer Overlap');
        tr.append('td').classed("metric", true).html(json['overlap_val']);
        tr.append('td').classed("metric", true).html(Number(json['overlap_score']).toFixed(numDigits));

        tr = tbl.append('tr');
        tr.append('td').html("Review Count Similarity");
        tr.append('td').classed("metric", true).html(json["review_sim_val"]);
        tr.append('td').classed("metric", true).html(Number(json["review_sim_score"]).toFixed(numDigits));

        tr = tbl.append('tr');
        tr.append("td").html("Ratings Similarity");
        tr.append('td').classed("metric", true).html(json['rate_sim_val']);
        tr.append('td').classed("metric", true).html(Number(json['rate_sim_score']).toFixed(numDigits));

        tr = tbl.append('tr');
        tr.append("td").html("Postal Code Match");
        tr.append('td').classed("metric", true).html(json['zip_val']);
        tr.append('td').classed("metric", true).html(Number(json['zip_score']).toFixed(numDigits));

        tr = tbl.append('tr');
        tr.append("td").html("Total");
        tr.append("td").html("");
        tr.append("td").classed("metric", true).html(Number(json['compete_score']).toFixed(numDigits));
    }
}

function clear_comparison_table() {
    var tag = d3.select(".similarity-container");
    tag.selectAll("table").remove();
    d3.select("#similarity-container-h3").html("&nbsp;");
    d3.select("#score-comparison-container-h3").html("&nbsp;");
}
function render_comparison_table(json, type) {
    var tag = d3.select(".similarity-container");
    tag.selectAll("table").remove();
    var tbl = tag.append("table");
    tbl.attr("id", "score_comparison_tbl").attr("style", "width:100%;");
    tbl.classed('display', true).classed('compact', true);
    var tr;
    var hdr1 = type == 'R' ? 'Competitor' : 'User';
    var hdr2 = type == 'R' ? "User's Rating" : 'Rating';
    var hdr3 = type == 'R' ? 'x Competitor Similarity' : 'x User Similarity';
    var hdr4 = '= Contribution';
    var col1 = type == 'R' ? 'restaurant' : 'user';
    var col2 = type == 'R' ? 'user_rating' : 'lmu_rating';
    var col3 = type == 'R' ? 'compete_score' : 'lmu_score';
    var col4 = type == 'R' ? 'contribution' : 'contribution';
    var colT = type == 'R' ? 'relevancy' : 'relevancy';

    var hdr = type == 'R' ? 'Customer Prospect Relevance': 'Recommended Restaurant Relevance';
    //var hdr = type == 'R' ? 'Relevance';
    d3.select("#similarity-container-h3").text(hdr);

    tr = tbl.append("thead").append("tr");
    tr.append("th").html(hdr1);
    tr.append("th").classed("metric",true).html(hdr2);
    tr.append("th").classed("metric",true).html(hdr3);
    tr.append("th").classed("metric",true).html(hdr4);

    tbl = tbl.append('tbody');

    // Render normal rows
    var sim_total=0, ctr_total=0, result;

    for (var i=0; i < json.length; i++) {
        tr = tbl.append('tr');
        tr.append('td').html(json[i][col1]);
        tr.append('td').classed("metric", true).html(json[i][col2].toPrecision(2));
        tr.append('td').classed("metric", true).html(json[i][col3].toPrecision(2));
        tr.append('td').classed("metric", true).html(json[i][col4].toPrecision(2));
        sim_total += json[i][col3];
        ctr_total += json[i][col4];
        result = json[i][colT];
    }

    tr = tbl.append('tr');
    tr.append('td').html("Totals");
    tr.append('td').html("");
    tr.append('td').classed("metric", true).html(sim_total.toPrecision(2));
    tr.append('td').classed("metric", true).html(ctr_total.toPrecision(2));

    tr = tbl.append('tr');
    tr.append('td').attr("colspan", "3").html("Contribution / Similarity");
    tr.append('td').classed("metric", true).html(result);
}



