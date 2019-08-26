## Setting up the development environment

### Development Applications

* Anaconda
* PyCharm


### Development Environment Setup

0. Note: If updating a previously installed environment, you first need to enter:

 conda remove --name bipolo-dev --all


1. How to initialize environment (Windows Version)

Start the Anaconda Command Prompt

``` cmdline

REM PROJECT_ROOT is the location of the cloned repository
REM For Doug's setup, set directory to f:
REM Then replace %PROJECT-ROOT% with f:\bipolo
conda env create -f %PROJECT_ROOT%/environment.yaml

REM Activate the bipolo-dev environment and change to root directory
activate bipolo-dev

```

2. How to find other package and include

    * use command 'conda search -c conda-forge <PKGNAME>
    * if found then add a line in the environment.yaml


3. How to update your current environment

```
conda env update -f %PROJECT_ROOT%/environment.yaml
 ```


4. How to start web server (For windows but easy to adapt for others)

```
%PROJECT_ROOT%\scripts\start_web_server.bat
 ```

HOW TO LAUNCH PROJECT

5. Open Chrome and enter the url http://127.0.0.1:5000/

6. Additionally you can navigate to http://127.0.0.1:5000/json_demo and enter json requests directly to see the data.
   For example enter either one of the following and click “Get JSON”
       /restaurant_profile/-jghjupgk9DVw5M-dCr3mw
       /user_profile/1sGYXSkJHPhJ6wQtc-RbZw
       
       

CSE6242 Project Readme.txt

1. DESCRIPTION - Describe the package in a few paragraphs.
 The functional modules are contained in the directory bipolo. This contains the python scripts that serve as the data layer 
 and buisiness logic layer. The templates directory within the bipolo directory contains the html, css, and javascript 
 files that generate  the user interface.
 
2. INSTALLATION - How to install and setup to run YUEGE.
   Clone the repository or otherwise copy the code to your local machine
   
   Install Anaconda package from https://www.anaconda.com/download/
   
   Open a terminal window and create a conda environment from the environment.yaml file in the base directory:
   ```
   conda env create -f environment.yaml
   ```
   Activate the environment:
   ```
   activate bipolo-dev
   ```
   Rename the CHANGEME file in the base directory to polo_config_local.py
   
   Open the polo_config_local.py and edit the following line with your AWS login username and password
   ```
   SQLALCHEMY_DATABASE_URI = 'mysql://yuegeguest:password$5@polodb.c3ffx89lowrn.us-east-2.rds.amazonaws.com/yelp_phoenix'
   ```
   Start the flask server by entering the scripts directory and running the startup batch file
   ```
   start_web_server.bat
   ```
 
3. EXECUTION - How to run a demo on your code.
  open a browser, preferably Chrome and enter the web address
   ```
   localhost:5000
   ```
