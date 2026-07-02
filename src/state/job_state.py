from typing_extensions import TypedDict, List
from langgraph.graph.message import add_messages
from typing import Annotated, Dict, Any

class JobState(TypedDict):
    """
    Represents the execution state of the Job Search Agent.
    """
    messages: Annotated[List, add_messages]
    resume_text: str
    job_type: str
    job_location: str
    date_posted_filter: str
    api_keys: Dict[str, str]
    extracted_profile: Dict[str, Any]
    search_url: str
    raw_jobs: List[Dict[str, Any]]
    matched_jobs: List[Dict[str, Any]]
