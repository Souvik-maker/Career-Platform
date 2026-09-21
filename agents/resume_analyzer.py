import json
import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from graph.state import AgentState

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
    api_key=os.getenv("GROQ_API_KEY")
)

def run_resume_analyzer(state: AgentState) -> AgentState:
    resume_text = state.get("resume_text", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert AI Resume Analyzer & Strict Document Classifier.

First, determine if the provided text is a VALID, serious, professional resume.

CRITICAL VALIDATION RULES:
1. Set "is_valid_resume": false if the document is fictional prose, a story, a book chapter, or an essay (e.g., fantasy/fiction writing)[cite: 4].
2. Set "is_valid_resume": false if the document is an unpopulated/blank template filled with bracket placeholders like "[YOUR FULL NAME]", "[Skill A]", or "[Company Name]"[cite: 5].
3. Set "is_valid_resume": false if the text contains joke entries, nonsensical claims, or completely lacks legitimate candidate details[cite: 6].
4. Set "is_valid_resume": true ONLY if it represents a genuine professional resume.

Output strictly valid JSON with no markdown formatting:
{{
    "is_valid_resume": true,
    "validation_reason": "Provide a brief explanation if invalid, else empty string",
    "skills": ["Python", "Docker", "SQL"],
    "certifications": ["AWS Certified Solutions Architect"],
    "experience_summary": "5 years of experience building backend systems...",
    "years_experience": 5.0
}}"""),
        ("user", "Resume Text:\n{resume_text}")
    ])
    
    chain = prompt | llm
    
    try:
        # Send sliced text for LLM analysis
        res = chain.invoke({"resume_text": resume_text[:4000]})
        raw_content = res.content.strip()
        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        
        if json_match:
            data = json.loads(json_match.group(0))
            is_valid = bool(data.get("is_valid_resume", False))
            val_reason = data.get("validation_reason", "Invalid resume format detected.")
            skills = data.get("skills", [])
            certifications = data.get("certifications", [])
            experience = data.get("experience_summary", "")
            years = float(data.get("years_experience", 0.0))
        else:
            is_valid = False
            val_reason = "Failed to parse structured resume data from document."
            skills, certifications, experience, years = [], [], "", 0.0
            
    except Exception as e:
        print(f"[RESUME PARSER ERROR]: {e}")
        is_valid = False
        val_reason = f"Error processing resume content: {str(e)}"
        skills, certifications, experience, years = [], [], "", 0.0

    return {
        **state,
        "is_valid_resume": is_valid,
        "validation_reason": val_reason,
        "parsed_skills": skills,
        "parsed_certifications": certifications,
        "candidate_experience": experience,
        "candidate_years": years
    }