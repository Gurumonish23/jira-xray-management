
from pydantic import BaseModel, Field
from typing import List

class JiraStory(BaseModel):
    summary: str = Field(..., description="Short summary of the user story")
    description: str = Field(..., description="Detailed story description")
    acceptance_criteria: str = Field(..., description="Acceptance criteria in Gherkin format")
    priority: str = Field(..., regex="^(High|Medium|Low)$", description="Priority level")
    story_points: int = Field(..., ge=1, le=13, description="Effort estimation in story points")
