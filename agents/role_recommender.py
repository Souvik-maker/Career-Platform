import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from graph.state import AgentState

# Load environment variables explicitly
load_dotenv()

# Pass api_key directly to ChatGroq
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY")
)

def run_role_recommender(state: AgentState) -> AgentState:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Tech Career Advisor. Suggest 3 matching industry job roles based on skills and experience. Output strictly a JSON array of strings: [\"Data Analyst\", \"Python Developer\"]"),
        ("user", "Skills: {skills}\nExperience: {experience}")
    ])
    
    chain = prompt | llm
    res = chain.invoke({
        "skills": state["parsed_skills"],
        "experience": state["candidate_experience"]
    })
    
    try:
        roles = json.loads(res.content)
    except Exception:
        roles = ["No Defined Roles"]
        
    return {**state, "recommended_roles": roles}