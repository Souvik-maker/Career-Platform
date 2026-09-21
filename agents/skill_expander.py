# agents/skill_expander.py
import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
    api_key=os.getenv("GROQ_API_KEY")
)

def expand_implied_skills(raw_skills: list) -> list:

    if not raw_skills:
        return []

    # Ensure input passed to LLM string formatting is a string/list, not a set
    skills_input = list(raw_skills) if isinstance(raw_skills, set) else raw_skills

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Lead Software Architect. Given a list of technical skills, deduce and expand all implicit foundational knowledge, framework components, and parent categories.

Expansion Rules:
- "Spring Boot" -> ["Spring Boot", "Spring Framework", "Spring MVC", "ORM", "Hibernate", "Java", "REST APIs"]
- "PostgreSQL" or "MySQL" -> ["PostgreSQL", "MySQL", "Relational Database", "RDBMS", "SQL"]
- "MongoDB" -> ["MongoDB", "NoSQL", "Document Database"]

Output ONLY a valid JSON list of strings containing both the original skills and all inferred implicit skills. Do not include markdown codeblocks or extra text."""),
        ("user", "Explicit Skills: {skills}")
    ])

    chain = prompt | llm
    try:
        res = chain.invoke({"skills": ", ".join(skills_input)})
        cleaned_content = res.content.strip().replace("```json", "").replace("```", "")
        parsed = json.loads(cleaned_content)
        # Convert to set for deduplication, BUT RETURN AS A LIST
        return list(set(parsed))
    except Exception:
        return list(skills_input)