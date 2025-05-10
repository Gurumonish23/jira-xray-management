
import os
import requests
from app.schemas.jira import JiraStory
from dotenv import load_dotenv

load_dotenv()

def create_jira_issue(story: JiraStory) -> dict:
    jira_url = os.getenv("JIRA_API_URL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    jira_email = os.getenv("JIRA_USER_EMAIL")
    project_key = os.getenv("JIRA_PROJECT_KEY", "LIG")

    headers = {
        "Authorization": f"Basic {jira_email}:{jira_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": story.summary,
            "description": f"{story.description}\n\nAcceptance Criteria:\n{story.acceptance_criteria}",
            "issuetype": {"name": "Story"},
            "priority": {"name": story.priority},
            "customfield_10002": story.story_points
        }
    }

    response = requests.post(jira_url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
