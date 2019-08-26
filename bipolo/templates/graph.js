///////////////////////////////////////////////////////////////////
//BiPolo Disorder Georgia Tech CSE6242 fall 2018 team project
//Copyright: Team BiPolo Disorder, 2018
//YUEGE explorer GUI viewer js
///////////////////////////////////////////////////////////////////

//refs d3 force directed graphs:
//https://bl.ocks.org/mbostock/4062045
//https://bl.ocks.org/mbostock/cd98bf52e9067e26945edd95e8cf6ef9
//https://bl.ocks.org/mbostock/950642
//https://stackoverflow.com/questions/40874162/d3-js-force-directed-graph-using-images-instead-of-circles-for-the-nodes
//refs manipulating nodes:
//https://stackoverflow.com/questions/10392505/fix-node-position-in-d3-force-directed-layout
//https://stackoverflow.com/questions/10502877/moving-fixed-nodes-in-d3
//https://github.com/d3/d3-force/blob/master/README.md#simulation_nodes
//https://stackoverflow.com/questions/17656502/d3js-create-a-force-layout-with-fixed-nodes
//https://stackoverflow.com/questions/13465796/d3-javascript-difference-between-foreach-and-each
//https://stackoverflow.com/questions/27405377/iterate-over-already-created-nodes-in-d3js
//refs reading json:
//http://bl.ocks.org/eyaler/10586116
//refs updating from json:
//http://bl.ocks.org/d3noob/7030f35b72de721622b8
//refs removing links and nodes:
//https://bl.ocks.org/mbostock/1095795
//refs for deque functions:
//http://www.i-programmer.info/programming/javascript/1674-javascript-data-structures-stacks-queues-and-deques.html?start=1
//refs for multiple svg containers:
//https://stackoverflow.com/questions/43203511/drag-drop-svg-element-between-svg-containers
//https://stackoverflow.com/questions/20141817/how-to-align-two-svgs-side-by-side-in-d3-js


// svg container for the graph
var svgGraph = d3.select("#graph")
    node = null; //graph nodes
    link = null; //graph links
var graph_svg = document.getElementById("graph");
//graph_svg.setAttribute("viewBox", "-400 -300 800 600"); //doesnt work on Tings computer, set viewbox in user_dashboard.html instead

var svgLegend = d3.select("#legend");

// svg left sidebar container for the history nodes
var history_div = document.getElementById("history-container");
var svgHistory = d3.select("#history")
	.attr("width", history_div.clientWidth)
	.attr("height", history_div.clientHeight);
    histNode = {}; //history nodes
	histDeque = new Deque();  // deque object for holding history node data

// svg left sidebar container for the profile table
var profile_div = document.getElementById("active-node-container");
//var svgProfile = d3.select("#profile")
//	.attr("width", history_div.clientWidth)
//	.attr("height", history_div.clientHeight);
	
// svg container for right side bar chart
var barchart_div = document.getElementById("score-comparison-container");
var svgBarChart = d3.select('#bar_chart')
	.attr("width", barchart_div.clientWidth)
	.attr("height", barchart_div.clientHeight);

// define the force simulation
var simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(function (d) {
        return d.id;
    }).strength(0.001))
	.force("charge", d3.forceCollide(10).radius(15))
    .force("r", d3.forceRadial(function(d) { return d.order * 70; }));
	
function render_graph(nodes, links) {
    // clear old data from svg
    if (node) {
        //console.log(node);
        node = node.data({}, function (d) {
            return d.id;
        });
        node.exit().remove();
    }

    if (link) {
        link = link.data({}, function (d) {
            //console.log(d.source.id + "-" + d.target.id);
            return d.source.id + "-" + d.target.id;
        });
        link.exit().remove();
    }
	
    // build links
    link = svgGraph.selectAll(".link").data(links, function (d) {
        return d.target.id;
    });
    link = buildLink();

    //build nodes
    node = svgGraph.selectAll(".node").data(nodes, function (d) {
        return d.id;
    });
    node = buildNode();

    //start simulation
    simulation.nodes(nodes).on("tick", ticked);
    simulation.force("link").links(links);
    simulation.alpha(1).restart();

    // add node to the history sidebar
    var activeNode = nodes.filter(node => node.order == 0)[0];
    pushHistoryNode(activeNode);
}

function ticked() {
    link.attr("x1", function (d) {
        return d.source.x;
    })
        .attr("y1", function (d) {
            return d.source.y;
        })
        .attr("x2", function (d) {
            return d.target.x;
        })
        .attr("y2", function (d) {
            return d.target.y;
        });
    node.attr("transform", function (d) {
        return "translate(" + d.x + ", " + d.y + ")";
    });
}

function dragstarted(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}

function dragended(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

function get_circle_css_class(node_info,type) {
    // Determine the css class to assign to the circle
    // given the specified node_info
	if (type == 'history'){
		if (node_info.type == "restaurant") {
			return "restaurant-circle0";
		} else if (node_info.type == "user") {
			return "user-circle0";
		} else {
			return "unknown-circle";
		}
	} else if (type == 'graph') {
		if (node_info.type == "restaurant") {
			return "restaurant-circle" + node_info.order;
		} else if (node_info.type == "user") {
			return "user-circle"+ node_info.order;
		} else {
			return "unknown-circle";
		}
    }
}

function color_links_to_active_node(d) {
	// Color the links that connect the selected node d to the active node

	var chain_links_indx_set = new Set([]);
	var chain_nodes_id_set = new Set([d.id]);
	// loop through each node order, collecting nodes and links in the chain that lead to the active node
	for (i = d.order; i != 0; i--) {
		link.each(function (l) {
			if (l.target.order == i){
				//console.log(d.order, l.source.order, l.target.order)
				// add the source node to the set if the target is or is linked to the selected node
				if (chain_nodes_id_set.has(l.target.id)) {
					chain_links_indx_set.add(l.index);
					chain_nodes_id_set.add(l.source.id);
				}
			}
		});
	}
	// color the links from selected to active node
	link.each(function (l) {
		if (chain_links_indx_set.has(l.index)) {
			d3.select(this).attr("stroke","green");
			d3.select(this).attr("stroke-width", 5);
		} else {
			d3.select(this).attr("stroke","#999");
			d3.select(this).attr("stroke-width", 1);
		}
	});
}

// add a node to the graph history sidebar
function pushHistoryNode(d) {
    histDeque.pushfront(d);
    histNode = svgHistory.selectAll(".nodes").data({}, function (d) {
        return d.id;
    });
    histNode.exit().remove();
    svgHistory.selectAll("*").remove();

    // load json node data into svg
    histNode = svgHistory.selectAll(".node").data(histDeque.stac, function (d) {
        return d.id;
    });
    histNode = histNode.enter()
        .append("g")
        .attr("class", "histNode");

    histNode.append("circle")
        .attr("r", 15)
        .attr("class", function (d) {
            return get_circle_css_class(d,"history");
        })
        .attr("cx", +svgHistory.attr("width") / 10)
        .attr("cy", function (d, i) {
            return i * 50 + 55;
        })
        .on("click", getHistNodeInfo)
        .on("dblclick", function (d) {
			var selidx = histDeque.indexof(d);
			if (selidx == 0) {
				// do nothing for now
			} else {
				histDeque.remove_priors(d);

				if (d.type == 'user') {
					controller.set_user_as_root(d.id);
				} else if (d.type == 'restaurant') {
					controller.set_restaurant_as_root(d.id);
				}
			}
        });

    histNode.append("text")
        .text(function (d) {
            return d.name
        })
		.attr("class","histNodeTitle")
        .attr("dx", +svgHistory.attr("width") / 6)
        .attr("dy", function (d, i) {
            return i * 50 + 60;
        })

}

// history sidebar mouse event handler:
function getHistNodeInfo(d) {
    //TODO: update sidebars or tooltip with HistNodeInfo
    console.log("getHistNodeInfo: " + d.name);
}

// graph builder helper function: build links, lines
function buildLink() {
    link = link.enter()
        .append("line")
        .attr("class", "link")
        .attr("stroke-width", 1)
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6);
    return link;
}

// graph builder helper function: build nodes, circles, text
function buildNode() {
    node = node.enter()
        .append("g")
        .attr("class", "node")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));
	
	var click_d = null;
	var dblclk_timout_ms = 400;
    node.append("circle")
        .attr("r", 15)
        .attr("class", function (d) {
            return get_circle_css_class(d,"graph");
        })
		.on("click", function (d) {
			// function to discriminate between single and double clicks
			// see: https://stackoverflow.com/questions/7897558/listen-to-double-click-not-click?noredirect=1&lq=1
			click_d = null
			click('notnull');
			function click(d){
				click_d = 'notnull'
				setTimeout(click_action, dblclk_timout_ms)
			}
			function click_action(){
				if(click_d == null){
					//console.log('single click cancelled')
					return
				} else {
					//console.log('single click fired')
					if (d.order != 0) {
						controller.show_graph_selected(d);
					}
				}
			}
		})
        .on("dblclick", function (d) {
			if (d.order != 0) {
				click_d = null
				//console.log('doubleclick fired')
				if (d.type == 'restaurant') {
					controller.selected_id = d.id
					controller.selected_type = 'R'
					controller.set_restaurant_as_root(d.id);
				} else if (d.type == 'user') {
					controller.selected_id = d.id
					controller.selected_type = 'U'
					controller.set_user_as_root(d.id);
				} else {
				}
			}
        });

    node.append("text")
        .text(function (d) {
            return d.name
        })
        .attr("dx", 0)
        //.attr("dy", "2.5em")
        .attr("dy", ".35em")
        .attr("font-family", "sans-serif")
        .attr("font-size", 10)
        //.attr("fill", "black");
		.attr("text-anchor", "middle")
	    .attr("fill", "black")
		.call(function (sel){
			sel.each(function(d) {d.bbox = this.getBBox();})
		});

    node.insert("rect", "text")
        .attr("x", function(d){return d.bbox.x})
        .attr("y", function(d){return d.bbox.y})
		.attr("width", function(d){return d.bbox.width})
    	.attr("height", function(d){return d.bbox.height})
        .style("stroke", "#cccccc")
		//.style("stroke-dasharray", "0.9")
        .style("fill-opacity", 0.6)
    	.style("fill", "white");
    return node;
}

// general purpose deque function - used for explorer history
function Deque() {
    this.stac = new Array();
    this.popback = function () {
        return this.stac.pop();
    }
    this.pushback = function (item) {
        this.stac.push(item);
    }
    this.popfront = function () {
        return this.stac.shift();
    }
    this.pushfront = function (item) {
        this.stac.unshift(item);
    }
    this.remove_priors = function(d) {
        while ((this.stac.length) && (this.stac[0]['id'] != d['id'])) {
            this.stac.shift();
        }
        // Remove the matching node too
        if (this.stac.length) {
            this.stac.shift();
        }
    }
    this.indexof = function(d) {
        for (var i=0; i < this.stac.length; i++) {
            if (d['id'] == this.stac[i]['id']) {
                return i;
            }
        }
        return -1;
    }
}

function clear_bar_chart() {
    svgBarChart.selectAll("*").remove();
}

function render_bar_chart(d, type) {
	//var div = d3.select(".score-comparison-container").append("div").attr("class", "toolTip");
	//console.log(d)
	// limit the number of records to show
	var numElements = Object.keys(d).length;
	var maxElements = 10;
	if (numElements > maxElements) {
		numElements = maxElements;
		data = d.slice(0, maxElements);
	} else {
		data = d;
	}

 	//check if selected node name is in the truncated data set
	var flag = false;
	for (var i = 0; i < data.length; i++) {
		if(data[i].name == controller.selected_name){
			flag = true;
		}
	}
	// if not in subset, then add it
	if (flag == false) {
		// get the index of the element in d corresponding to selected
		var index = -1;
		for (var i = 0; i < d.length; i++) {
			if(d[i].name == controller.selected_name){
				index = i;
			}
		}
		// append selected record to the array
		if (index > -1) {
			data = d.slice(0, maxElements-1);
			data.push(d[index]);
		}
	}

    var axisMargin = 5,
		margin = 3,
		valueMargin = 2,
		bchwidth = parseInt(d3.select('#bar_chart').style('width')),
		bchheight = parseInt(d3.select('#bar_chart').style('height')),
		barHeight = (bchheight-axisMargin-margin *2) * 0.3/(maxElements),
		barPadding = (bchheight-axisMargin-margin * 2) * 0.2/(maxElements),
		data, bar, svg, scale, xAxis, labelWidth = 0;

	var max = 5;
	var x = d3.scaleLinear()
          .range([0, bchwidth - margin * 4]);
	var y = d3.scaleBand()
          .range([bchheight - 2 * margin, 0]);
    x.domain([0, max]);
	y.domain(data.map(function(d) { return d.name; }));

	var bar = svgBarChart.selectAll("g")
		.data(data)
		.enter().append("g")
		.attr("transform", function(d, i) { return "translate(0," + i * barHeight + ")";});
		
	bar.append("rect")
		.attr("class", "bar_rect")
		.attr("x", function(d) { return margin; })
		.attr("width", function(d){ return x(d.score); })
		.attr("y", function(d, i) { return i * (barHeight) ; })
		.attr("height", barHeight);

	bar.append("text")
		.attr("class", "bar_text")
        .attr("x", margin)
		.attr("y", function(d, i) { return i * (barHeight) + 4; })
        .attr("dy", barHeight + barPadding/2 + margin)
		.text(function (d) { return d.name; })

	/*
	bar.append("text")
		.attr("class", "bar_text")
        .attr("x", margin)
		.attr("y", function(d, i) { return i * (barHeight) + 15; })
        .attr("dy", barHeight + barPadding/2 + margin)
		.text(function (d) { return d.name; })
	*/

	bar.append("text")
		.attr("class", "bar_score_text")
        .attr("x", function(d){ return x(d.score) - 45; })
		.attr("y", function(d, i) { return i * (barHeight) + 6 +barHeight/2; })
        //.attr("dy", margin)
		.text(function (d) { return Number(d.score).toFixed(2); });
		
	// highlight the bar corresponding to the selected graph node
	var gbars = svgBarChart.selectAll("rect");
	id = ''
	gbars.each(function(d) {
		//console.log(d.name, profile[0].name)
		if (d.name == controller.selected_name) {
			//console.log(type)
			if (type == 'R') {
				d3.select(this).classed("bar_rect_Rselected", true);
			} else {
				d3.select(this).classed("bar_rect_Uselected", true);
			}
		}
	});

	//console.log(bar)

}
