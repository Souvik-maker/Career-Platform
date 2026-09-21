from utils.job_api import fetch_jobs_adzuna_india
from graph.state import AgentState

def run_job_search(state: AgentState) -> AgentState:
    "Agent 3: Fetches raw job listings based on selected role."
    role = state.get("selected_role", "Software Engineer")
    location = state.get("selected_location", "India")
    
    jobs = fetch_jobs_adzuna_india(role=role, location=location, results_per_page=5)
    return {**state, "raw_job_listings": jobs}