import os
import requests
from dotenv import load_dotenv

load_dotenv()

def fetch_jobs_adzuna_india(role: str, location: str = "India", results_per_page: int = 5) -> list:
    """
    Fetches real live job listings in India using the Adzuna Free Public API.
    If API credentials are not found in .env, falls back to structured mock data.
    """
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    
    # Fallback mock data if API keys are missing or empty
    if not app_id or not app_key:
        print("[INFO] ADZUNA_APP_ID or ADZUNA_APP_KEY not set. Using local mock job listings.")
        return [
            {
                "company": "TCS (Tata Consultancy Services)",
                "title": f"Senior {role}",
                "location": location if location != "India" else "Bengaluru",
                "description": f"We are looking for a qualified {role} with expertise in Python, SQL, Docker, AWS, and Git. Excellent communication and problem-solving skills required."
            },
            {
                "company": "Infosys",
                "title": f"{role} Specialist",
                "location": location if location != "India" else "Hyderabad",
                "description": f"Hiring for {role} position. Required technical stack: Python, Django, REST APIs, Microservices, Kubernetes, and Agile methodology experience."
            },
            {
                "company": "Wipro",
                "title": f"Associate {role}",
                "location": location if location != "India" else "Pune",
                "description": f"Key skills required: Python, Data Structures, FastAPI, SQL Databases, and basic Linux administration. Understanding of CI/CD pipelines is a plus."
            }
        ]
        
    # Adzuna API URL configured for India region ('in')
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": results_per_page,
        "what": role,
        "where": location
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get("results", []):
                results.append({
                    "company": item.get("company", {}).get("display_name", "Unknown Company"),
                    "title": item.get("title", role),
                    "location": item.get("location", {}).get("display_name", location),
                    "description": item.get("description", "")
                })
            return results
        else:
            print(f"[WARNING] Adzuna API returned status code {response.status_code}. Using fallback mock data.")
    except Exception as e:
        print(f"[ERROR] Exception during Adzuna API request: {e}")
        
    # Fallback if request fails
    return [
    ]