import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.3,
    api_key=os.getenv("GROQ_API_KEY")
)
# Resume Tailoring and Market Report Generation
def generate_tailored_resume(original_resume: str, job_title: str, company: str, job_description: str, matching_skills: list, missing_skills: list) -> str:
    """Generates an ATS-optimized, tailored markdown resume for a target job posting."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Resume Writer and ATS Specialist. Rewrite the candidate's resume to specifically target the specified role and company. Strategically highlight matching skills and naturally incorporate missing required skills where plausible under candidate achievements. Return a clean, professional Markdown resume."),
        ("user", "Target Job Title: {job_title}\nCompany: {company}\nJob Description:\n{job_description}\n\nMatching Skills: {matching_skills}\nMissing Skills to weave in: {missing_skills}\n\nOriginal Resume:\n{original_resume}")
    ])
    
    chain = prompt | llm
    res = chain.invoke({
        "job_title": job_title,
        "company": company,
        "job_description": job_description,
        "matching_skills": ", ".join(matching_skills),
        "missing_skills": ", ".join(missing_skills),
        "original_resume": original_resume
    })
    
    return res.content
# Generate Market Analysis Report
def generate_market_report(skills: list, experience: str, target_role: str) -> str:
    """Generates a realistic future trajectory and Indian market analysis report."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Lead Market Intelligence Strategist for tech careers. Produce a structured analysis report covering:
1. Realistic Future: Immediate & 3-5 Year realistic trajectory if the candidate stays in this track.
2. In-Demand Skills Assessment: Which current skills are high-value in today's tech market.
3. Market Radar: Trending market demands and emerging tools required for growth.
Output as a polished, formatted report."""),
        ("user", "Candidate Skills: {skills}\nExperience Level: {experience}\nCurrent/Target Role: {target_role}")
    ])
    
    chain = prompt | llm
    res = chain.invoke({
        "skills": ", ".join(skills),
        "experience": experience,
        "target_role": target_role
    })
    
    return res.content