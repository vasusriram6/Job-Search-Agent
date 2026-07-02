import urllib.parse
from src.state.job_state import JobState

class JobSearchUrlNode:
    def process(self, state: JobState) -> dict:
        profile = state.get("extracted_profile", {})
        keyword = profile.get("job_search_keyword", "Software Engineer")
        location = state.get("job_location", "") or profile.get("preferred_location", "Remote")
        
        encoded_keyword = urllib.parse.quote(keyword)
        encoded_location = urllib.parse.quote(location)
        
        search_url = f"https://www.google.com/search?q={encoded_keyword}+jobs+in+{encoded_location}&ibp=htl;jobs"
        return {"search_url": search_url}
