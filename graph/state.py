from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    resume_id: Optional[int]
    file_name: str
    resume_text: str
    parsed_skills: List[str]
    parsed_certifications: List[str]
    candidate_experience: str
    candidate_years: float
    recommended_roles: List[str]
    selected_role: Optional[str]
    selected_location: Optional[str]
    raw_job_listings: List[Dict[str, Any]]
    parsed_jobs: List[Dict[str, Any]]
    match_results: List[Dict[str, Any]]