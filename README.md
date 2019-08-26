# Data-Visualization-Analytics
CSE6242 Project Readme.txt

###############################################################
DESCRIPTION
###############################################################

The package is a copy of our github repository used during the development of the YUEGE application. The repository
is private but is hosted at https://github.gatech.edu/bsmith419/bipolo. This package is explained as follows:

Technical Summary:
The bipolo project is a flask web application. The web application connects to a MySQL database which contains the
Yelp database. Python 2.7 was chosen as the interpreter and Anaconda was selected as the dependency/package manager.
The primary python packages used are flask, pandas, sqlachemy, and the MySQL driver. The web server delivers
a single-page web application for visualizations and user interactions. The client html leverages the javascript
libraries d3, jquery, and select2. These libraries are delivered via their respective CDNs and the client communicates
with the web server via JSON requests.

Environment:
The environment.yaml defines the packages necessary for the python environment and requires
Anaconda. In addition to the environment.yaml, there is a polo_config_local.py which provides the
configuration for the database connection string.

Source Code:
The 'bipolo' directory is a python module that contains the code which serves as the data layer and business logic layer.
Below I will list the core files and a brief explanation of their funcionality/role in the application.

bipolo/alogorithm.py: Contains the core data access layer
bipolo/api.py: Provides the main business logic by aggregating calls to the algorithm.py and exposing them as an API
bipolo/view.py: Web server entry points (aka urls) which invoke the api, collects the data, and transforms the
                results into JSON for client consumption.
bipolo/run.py: Starts the flask server
bipolo/templates/user_dashboard.html:  Single-page HTML application which communicates with the server via JSON calls.
bipolo/templates/bipolo.css: Style sheet for the HTML application
bipolo/templates/bipolo.js: Provides the primary ui controller for the HTML application
bipolo/templates/graph.js:  Builds the core graph explorer using d3 in the HTML application


###############################################################
INSTALLATION
###############################################################

1. Ensure Anaconda is installed as it is used to install the python environment and resolve package dependencies
   (https://conda.io/docs/user-guide/install/index.html)

2. Create the python environment for bipolo project by running `conda env create -f environment.yaml`

3. Database setup. We have setup a database on AWS or the database can be installed locally for optimal performance. To
    use the AWS database just ensure that the polo_config_local.py has the following configuration entry:
    SQLALCHEMY_DATABASE_URI = 'mysql://yuegeguest:password$5@polodb.c3ffx89lowrn.us-east-2.rds.amazonaws.com/yelp_phoenix'

    To install a local version, install MySQL locally and then download and import the Yelp Phoenix database from
    https://s3.us-east-2.amazonaws.com/cse6242oan-bipolodisorder/YelpPhoenix.sql
    Once the local database is setup, modify the SQLALCHEMY_DATABASE_URI to point to the local database.

4. Activate the bipolo environment as follows:
   On Windows, "activate bipolo-dev"

5. Start the flask server
   On Windows, at command prompt with bipolo-dev active, run the "scripts\start_web_server.bat" file


###############################################################
EXECUTION
###############################################################

With flask server running, open Chrome and enter the web address:  http://localhost:5000
