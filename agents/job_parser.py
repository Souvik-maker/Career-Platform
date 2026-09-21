import json
import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from graph.state import AgentState
from agents.skill_expander import expand_implied_skills
from utils.matcher import evaluate_composite_fit

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
    api_key=os.getenv("GROQ_API_KEY")
)

def clean_jd_text(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', cleaned).strip()

def run_job_parser(state: AgentState) -> AgentState:
    cand_skills = expand_implied_skills(state.get("parsed_skills", []))
    cand_certs = state.get("parsed_certifications", [])
    cand_years = float(state.get("candidate_years", 0.0))
    hide_below_exp = bool(state.get("hide_below_exp", False))
    
    parsed_jobs = []
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Job Description Parser.
Extract technical skills, certifications, and required years of experience from the job post.

CRITICAL INSTRUCTIONS:
1. Extract all explicitly mentioned technical skills, tools, and frameworks.
2. If the Job Description lacks an explicit skills section, infer up to 3-5 standard core skills based on the Job Title (e.g., if Title is 'Backend Engineer', infer ['REST API', 'Databases', 'Backend Development']).
3. Output strictly valid JSON:
{{
    "required_skills": ["Python", "REST API"],
    "required_certifications": [],
    "required_years_experience": 2.0
}}"""),
        ("user", "Job Title: {title}\nJob Description:\n{description}")
    ])
    
    chain = prompt | llm

    for job in state.get("raw_job_listings", []):
        cleaned_desc = clean_jd_text(job.get("description", ""))
        
        try:
            res = chain.invoke({
                "title": job.get("title", ""),
                "description": cleaned_desc[:6000]
            })
            
            raw_content = res.content.strip()
            json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group(0))
                job_skills = data.get("required_skills", [])
                job_certs = data.get("required_certifications", [])
                req_years = float(data.get("required_years_experience", 0.0))
            else:
                job_skills, job_certs, req_years = [], [], 0.0
                
        except Exception as e:
            print(f"[JOB PARSER ERROR]: {e}")
            job_skills, job_certs, req_years = [], [], 0.0

        # --- EXPERIENCE FILTERING CHECK ---
        if hide_below_exp and cand_years >= 3.0 and req_years <= 0.5:
            continue  # Skip jobs far below candidate's experience level

        # Run Composite Fit Evaluation
        eval_metrics = evaluate_composite_fit(
            candidate_skills=cand_skills,
            candidate_certs=cand_certs,
            candidate_years=cand_years,
            job_skills=job_skills,
            job_certs=job_certs,
            required_years=req_years
        )

        parsed_jobs.append({
            "company": job.get("company", ""),
            "title": job.get("title", ""),
            "location": job.get("location", ""),
            "description": cleaned_desc,
            "required_skills": job_skills,
            "required_certifications": job_certs,
            "required_years_experience": req_years,
            "evaluation": eval_metrics,
            "match_score": eval_metrics["final_score"]
        })

    # Sort descending by overall match score
    sorted_jobs = sorted(parsed_jobs, key=lambda x: x["match_score"], reverse=True)

    return {**state, "parsed_jobs": sorted_jobs}