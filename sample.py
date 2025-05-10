import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
load_dotenv()
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")

url = "https://student-team-ah44ljbt.atlassian.net/rest/api/3/myself"
headers = {"Accept": "application/json"}

response = requests.get(url, headers=headers, auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN))

if response.status_code == 200:
    data = response.json()
    print("Your reporter_id (accountId):", data["accountId"])
else:
    print("Error:", response.text)
