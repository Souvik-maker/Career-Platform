from langgraph.graph import StateGraph, END
from graph.state import AgentState

# Phase 1 Agents
from agents.resume_analyzer import run_resume_analyzer
from agents.role_recommender import run_role_recommender

# Phase 2 Agents
from agents.job_search_agent import run_job_search
from agents.job_parser import run_job_parser

# Phase 3 Agent
from agents.skill_gap_agent import run_skill_gap_analysis

def build_phase1_pipeline():
    "Phase 1: Resume Analysis -> Role Recommendation."
    workflow = StateGraph(AgentState)
    workflow.add_node("resume_analyzer", run_resume_analyzer)
    workflow.add_node("role_recommender", run_role_recommender)
    
    workflow.set_entry_point("resume_analyzer")
    workflow.add_edge("resume_analyzer", "role_recommender")
    workflow.add_edge("role_recommender", END)
    return workflow.compile()

def build_phase2_pipeline():
    "Phase 2: Job Search -> Job Parsing."
    workflow = StateGraph(AgentState)
    
    workflow.add_node("job_search", run_job_search)
    workflow.add_node("job_parser", run_job_parser)
    
    workflow.set_entry_point("job_search")
    workflow.add_edge("job_search", "job_parser")
    workflow.add_edge("job_parser", END)
    return workflow.compile()

def build_phase3_pipeline():
    "Phase 3: Skill Gap Analysis & Match Scoring Pipeline."
    workflow = StateGraph(AgentState)
    workflow.add_node("skill_gap_analysis", run_skill_gap_analysis)
    workflow.set_entry_point("skill_gap_analysis")
    workflow.add_edge("skill_gap_analysis", END)
    return workflow.compile()