import streamlit as st 
import pandas as pd
import openai
import os
from dotenv import load_dotenv
import pandas as pd
import json
import requests
import re
from collections import Counter
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def fetch_user_repositories(user_url):
    username = user_url.split('/')[-1]  # Extract the username from the URL
    response = requests.get(f'https://api.github.com/users/{username}/repos', headers={'Authorization': f'token {GITHUB_TOKEN}'})
    #print(f"ye rha {response}")
    if response.status_code == 200:
        return response.json()
    else:
        print("Error response from GitHub API:", response.text)
        return []




def analyze_complexity_with_gpt(repo_detail):
    
    message = [
        {"role": "system", "content": "you are an ai assistant your job is to find the complexity of  Github repositories of user."},
        {"role": "system", "content": "you are provided with information like repo_id , description ,language, size ,stargazers_count ,watchers_count ,forks_count ,open_issues_count,line of code, contribution count, library used,commits count  "},
        {"role": "system", "content": "analyze all the provided information and give a complexity score , the higher the score the more complex the repository is, the score should be between 1-100"},
        {"role": "system", "content": "only return a number between 1 to 100 no texts"},       
        {"role": "user", "content": "repo_id , description ,language, size ,stargazers_count ,watchers_count ,forks_count ,open_issues_count,line of code, contribution count, library used,commits count  "},
        {"role": "assistant", "content": "consider all the factors and return complexity score, the higher the number the higher the complexity"},
        {"role": "user", "content": repo_detail}
    ]


    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0.8,
        messages=message
    )
    return response['choices'][0]['message']['content']

def generate_repo_report(repository_data):
    repo_report = {}
    
    for repo in repository_data:
        repo_id = repo['id']
        owner_login = repo['owner']['login']
        repo_name = repo['name']
        repo_link = f"https://github.com/{owner_login}/{repo_name}"  # Constructing the repository link
        description = repo['description']
        language = repo['language']
        size = repo['size']
        stargazers_count = repo['stargazers_count']
        watchers_count = repo['watchers_count']
        forks_count = repo['forks_count']
        open_issues_count = repo['open_issues_count']
            
        
        # Additional attributes that might indicate complexity
        commits_count = get_commits_count(repo_name, owner_login)  # Replace with actual function to get commits count
        contributors_count = get_contributors_count(repo_name, owner_login)  # Replace with actual function to get contributors count
        libraries_used = get_libraries_used(repo_name, owner_login) 
        lines_of_code = get_lines_of_code(repo_name, owner_login)
        # Create a dictionary with relevant information for the repository
        repo_info = (
            f'{{'
            f'"name": "{repo_name}", '
            f'"description": "{description}", '
            f'"language": "{language}", '
            f'"size": {size}, '
            f'"stargazers_count": {stargazers_count}, '
            f'"watchers_count": {watchers_count}, '
            f'"forks_count": {forks_count}, '
            f'"open_issues_count": {open_issues_count}, '
            f'"commits_count": {commits_count}, '
            f'"contributors_count": {contributors_count}, '
            f'"libraries_used": {json.dumps(libraries_used)},'
            f'"lines_of_code": {lines_of_code}'
            f'}}'
        )
        
        # Store the repository information in the report dictionary
        repo_report[repo_link] = repo_info
    
    return repo_report

def get_commits_count(repo_name, owner):
    url = f"https://api.github.com/repos/{owner}/{repo_name}/commits"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        commits = response.json()
        return len(commits)
    else:
        return 0

def get_contributors_count(repo_name, owner):
    url = f"https://api.github.com/repos/{owner}/{repo_name}/contributors"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        contributors = response.json()
        return len(contributors)
    else:
        return 0
def get_lines_of_code(repo_name, owner):
    url = f"https://api.github.com/repos/{owner}/{repo_name}/stats/code_frequency"
    response = requests.get(url)
    
    if response.status_code == 200:
        code_frequency = response.json()
        total_lines_added = sum(entry[1] for entry in code_frequency)
        total_lines_deleted = sum(entry[2] for entry in code_frequency)
        total_lines_of_code = total_lines_added - total_lines_deleted
        return total_lines_of_code
    else:
        return None  # Failed to fetch lines of code

def get_libraries_used(repo_name, owner):
    url = f"https://api.github.com/repos/{owner}/{repo_name}/contents"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    
    libraries_used = Counter()  # Using Counter to count library occurrences
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        contents = response.json()
        for item in contents:
            if item["type"] == "file" and item["name"].endswith(".py"):
                file_url = item["download_url"]
                file_contents = requests.get(file_url).text
                imports = re.findall(r'^\s*import\s+([\w\d_]+)', file_contents, re.MULTILINE)
                for library in imports:
                    libraries_used[library] += 1
    else:
        print("Error:", response.text)
    
    return libraries_used

repo_scores={}
if __name__ == "__main__":
    
    st.title("GitHub Repository Complexity Analyzer")
    user_url = st.text_input("enter github user url")
    if st.button("Analyze"):
        repositories = fetch_user_repositories(user_url)
        #print(repositories)
         # Save the repositories data as a JSON file
        with open("repositories_data.json", "w") as json_file:
            json.dump(repositories, json_file, indent=4)
        print("repo extracted")    
        #convert repo to repo description dictionary to be give to prompt
        repo_desc={}
        repo_desc= generate_repo_report(repositories)
        print("repo desc extracted")
        #print(repo_desc)
        if not repositories:
            st.write("No repositories found for the provided user URL.")
        else:
            print("to calc repo score")
            for repo_link, repo_info in repo_desc.items():
                repo_scores[repo_link] = analyze_complexity_with_gpt(repo_info)
                print(repo_link,repo_scores[repo_link])
        # # Display the results in the repo_scores dictionary
        #     for repo_link, score in repo_scores.items():
        #         st.write(f"Repository: {repo_link}")
        #         st.write(f"Complexity Score: {score}")
                
            # Find the repository link with the highest complexity score
            most_complex_repo_link = max(repo_scores, key=repo_scores.get)

            # Print the most complex repository link
            st.write("Most Complex Repository:")
            st.write(f"Repository: {most_complex_repo_link}")
            st.write(f"Complexity Score: {repo_scores[most_complex_repo_link]}")
            