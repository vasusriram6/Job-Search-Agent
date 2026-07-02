from pydantic import BaseModel, Field
from typing import List, Optional

class JobQueryExtractor(BaseModel):
    """
    Structured extraction of candidate profiles from resume text and/or job query.
    """
    skills: List[str] = Field(description="List of primary technical and soft skills extracted.")
    experience_level: str = Field(description="Candidate experience level, e.g., Entry-level, Junior, Mid, Senior, Lead, Executive.")
    preferred_location: str = Field(description="Preferred location or Remote/Hybrid preference.")
    job_search_keyword: str = Field(description="Optimal job search keyword/term for searching job boards.")
    experience_summary: str = Field(description="Brief summary of overall professional experience.")

class JobListing(BaseModel):
    """
    Structured job listing data retrieved from LinkedIn or Search.
    """
    title: str = Field(description="Job Title")
    company: str = Field(description="Company offering the job")
    location: str = Field(description="Job location")
    link: str = Field(description="Direct URL link to the job listing")
    description: str = Field(description="Detailed description of the job requirements and responsibilities")
    snippet: Optional[str] = Field(default=None, description="Short snippet of the job listing description")
    posted_at: Optional[str] = Field(default=None, description="When the job was posted")

class JobMatchResult(BaseModel):
    """
    Structured job match evaluation output.
    """
    title: str = Field(description="Job Title")
    company: str = Field(description="Company offering the job")
    location: str = Field(description="Job location")
    link: str = Field(description="Direct URL link to the job listing")
    posted_at: Optional[str] = Field(default=None, description="When the job was posted")
    match_score: float = Field(description="Match percentage/similarity score between candidate and job requirements (0 to 100)")
    match_explanation: str = Field(description="Clear explanation on why this job is a match and how it fits the candidate's profile.")

class JobMatchResultsList(BaseModel):
    """
    List container for structured job match results.
    """
    matches: List[JobMatchResult] = Field(description="List of evaluated job match results.")

