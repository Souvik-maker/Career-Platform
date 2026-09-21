import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from graph.state import AgentState
from agents.skill_expander import expand_implied_skills
from utils.semantic_matcher import calculate_semantic_match

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY")
)

def run_skill_gap_analysis(state: AgentState) -> AgentState:
    raw_candidate_skills = state.get("parsed_skills", [])
    expanded_candidate_skills = expand_implied_skills(raw_candidate_skills)
    parsed_jobs = state.get("parsed_jobs", [])
    
    results = []
    
    prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Tech Career Advisor. Analyze the skill gap between candidate and job requirements. Provide actionable recommendations. DO NOT use raw HTML tags like <br> inside tables or markdown. Use clean Markdown bullet points or standard newline spacing."),
    ("user", "Candidate Skills: {candidate_skills}\nJob Title: {job_title}\nCompany: {company}\nMissing Skills: {missing_skills}")
])
    chain = prompt | llm

    for job in parsed_jobs:
        job_skills = set(s.strip().lower() for s in job.get("required_skills", []))
        
        # Calculate consistent semantic match
        match_score, matched_display, missing_display = calculate_semantic_match(
            candidate_skills=expanded_candidate_skills,
            job_required_skills=job_skills,
            threshold=0.65
        )

        res = chain.invoke({
            "candidate_skills": ", ".join(raw_candidate_skills),
            "job_title": job.get("title", ""),
            "company": job.get("company", ""),
            "missing_skills": ", ".join(missing_display) if missing_display else "None"
        })
        
        results.append({
            "company": job.get("company", ""),
            "job_title": job.get("title", ""),
            "match_score": match_score,
            "matched_skills": matched_display,
            "missing_skills": missing_display,
            "description": job.get("description", ""),
            "recommendation": res.content
        })

    # Sort job matches by match score descending (Priority Order)
    sorted_results = sorted(results, key=lambda x: x["match_score"], reverse=True)

    return {**state, "match_results": sorted_results}