import pkg_resources
import time
import json
import math
import pycurl
import certifi
from io import BytesIO
from docassemble.base.util import as_datetime

#-----------------------------------------------------
# Extract server name
#-----------------------------------------------------
def get_server_name(interview_url):
  begin = interview_url.find('//') + 2
  end = interview_url.find('/interview?')
  
  return interview_url[begin:end]

#-----------------------------------------------------
# Crawl installed packages on the current server.
# Store key and non key docassemble packages separately.
#-----------------------------------------------------
def installed_pkg_list(target: list) -> dict: 
  installed_packages = {}
  key_packages = {}
  non_key_packages = {}  
  
  for p in pkg_resources.working_set:              
      # docassemble packages
      if 'docassemble' in p.project_name:   
        # Key packages
        if p.project_name in target:                     
          key_packages[p.project_name] = p.version
        # non-key packages
        if p.project_name not in target:
          non_key_packages[p.project_name] = p.version      
      
  sorted_key_packages = sort_dict(key_packages)
  sorted_non_key_packages = sort_dict(non_key_packages)
  
  installed_packages['key_pkgs'] = sorted_key_packages
  installed_packages['non_key_pkgs'] = sorted_non_key_packages  
  
  return installed_packages

def sort_dict(raw_data: dict):
  return dict( sorted(raw_data.items(), key=lambda x: x[0].lower()) )
  
#-----------------------------------------------------
# Crawl github packages (default branch) under a given github user name
#-----------------------------------------------------
# Borrowed ideas from https://github.com/rsain/GitHub-Crawler
# It's 4 years old and broken, but the structure is still valid. 
#
# The GitHub API limits the queries to get 100 elements per page and up to 1,000 elements in total.
# To get more than 1,000 elements, the main query should be split in multiple subqueries 
# using different time windows through sub_queries (a list of subqueries).
#
# The original had a comment that DELAY_BETWEEN_QUERYS is used to avoid be banned - Is this still valid?
# See documentation regarding Github Search API limitations:  
# https://docs.github.com/en/rest/reference/search
# https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting

URL = "https://api.github.com/search/repositories?q=" #The basic URL to use the GitHub API
PARAMETERS = "&per_page=100" #Additional parameters for the query (by default 100 items per page)
DELAY_BETWEEN_QUERYS = 3 #The time to wait between different queries to GitHub 

def getUrl (url) :
  ''' Given a URL it returns its body '''
  buffer = BytesIO()
  c = pycurl.Curl()
  c.setopt(c.URL, url)
  c.setopt(c.WRITEDATA, buffer)
  c.setopt(c.CAINFO, certifi.where())
  c.perform()
  c.close()
  body = buffer.getvalue()
  # Body is a byte string.
  # We have to know the encoding in order to print it to a text file.    
  return body.decode('iso-8859-1')

def fetch_github_repos (github_user, sub_queries) -> dict:
  ''' Given a github user input, returns soughted info. It doesn't contain version number. '''  
  repositories = {}

  # Run queries to get information in json format and download ZIP file for each repository
  for subquery in range(1, len(sub_queries)+1):
	
    #Obtain the number of pages for the current subquery (by default each page contains 100 items)
    url = URL + github_user + str(sub_queries[subquery-1]) + PARAMETERS			
    dataRead = json.loads(getUrl(url))	
    numberOfPages = int(math.ceil(dataRead.get('total_count')/100.0))
    
    #Results are in different pages
    for currentPage in range(1, numberOfPages+1):
      url = URL + github_user + str(sub_queries[subquery-1]) + PARAMETERS + "&page=" + str(currentPage)
      dataRead = json.loads(getUrl(url))
    
      #Iteration over all the repositories in the current json page [a list of dicts]
      for repo in dataRead['items']:        
        repositories[repo['name']] = {
          'branch_name': repo['default_branch'],
            'created_date': as_datetime(repo['created_at']).format_date(),
            'push_date': as_datetime(repo['pushed_at']).format_date(),
            'open_issues_count': repo['open_issues_count'], 
            'repo_url': repo['html_url'],            
          }                   
        
    # A delay between different subqueries
    if (subquery < len(sub_queries)):		  
      time.sleep(DELAY_BETWEEN_QUERYS)
  return sort_dict(repositories)

def fetch_github_repo_version(repo_list, key_pkgs, github_user) -> dict:
    """Grab github repo version number in setup.py and add it to the input repo_list
    Separate the pile into key repos/non-key repos & sort each, then store them in a new nested dict.
    """
  import requests

  github_repos = {} # Parent dict
  key_repos = {} # Child dict
  nonkey_repos = {} # Child dict  
  
  github_key_pkg_names = [a.replace('.', '-') for a in key_pkgs] 

  for k, v in list(repo_list.items()):  
    # Construct url for repo's setup.py file      
    setup_py_URL = 'https://raw.githubusercontent.com/' + github_user + '/' + k + '/' + v['branch_name'] + '/setup.py'    

    # Fetch file content      
    file_content = requests.get(setup_py_URL)

    # Not every package has a setup.py file
    if file_content.text:
      # Find the line containing "version=" and copy the version number
      for line in file_content:
        decoded_line = line.decode("utf-8")      
        if 'version=' in decoded_line:          
          str_start = decoded_line.find('version=') 
          str_end = decoded_line.find('description') 
          version_num = decoded_line[str_start:str_end][9:].replace('\',\n', '')  
          v['version'] = version_num # Add version number to the original repo_list.          
          break   
  
    # Separate key pkgs from non-key pkgs and save them into new dicts
    if k in github_key_pkg_names:
      key_repos[k] = v #copy the record into key_repos
    else:      
      if 'version' in repo_list.keys(): # Only care about repos with version#/setup.py
        nonkey_repos[k] = v #copy the record into nonkey_repos
  
  # Store the sorted new repos into the parent dict
  github_repos['key_repos'] = sort_dict(key_repos)  
  github_repos['non_key_repos'] = sort_dict(nonkey_repos) 
  
  return github_repos

#-----------------------------------------------------
# Compare server repo version with github repo version
# Return the results as a dict for screen display
#-----------------------------------------------------
def compare_repo_version(server_repo_dict, github_repo_dict) -> dict:
  version_table = {}
  for k1, v1 in server_repo_dict.items(): # Loop thru server repos
    version_table[k1] = {'server': v1, 'github': 'No new commit'}     
    
    if len(github_repo_dict) > 0: # If there are any commits in the period
      for k2, v2 in github_repo_dict.items():       
        if k1 == k2.replace('-', '.'): # If repo match is found
          if v1 in v2['version']:  # Check its version
            # Override the version info in the table record
            version_table[k1] = {'server': v1, 'github': v2['version']}  
          else: # Override the not-matched version info with an alert sign
            version_table[k1] = {'server': v1 + ' &#9940', 'github': v2['version']} 
    
  return version_table