import re
import streamlit as st
from dotenv import load_dotenv
from database import (
    init_db, save_initial_resume, update_resume_analysis, 
    save_parsed_jobs, save_match_results, save_generated_resume, save_market_report
)
from utils.pdf_parser import extract_text_from_file
from graph.workflow import build_phase1_pipeline, build_phase2_pipeline, build_phase3_pipeline
from agents.report_generator import generate_tailored_resume, generate_market_report
from utils.pdf_generator import generate_resume_html, generate_pdf_bytes_from_html, generate_pdf_bytes


# --- HELPER FUNCTIONS FOR CLEAN TEXT & MARKDOWN ---
def clean_markdown_output(text: str) -> str:
    if not text:
        return ""
    # Replace HTML line breaks with clean markdown line breaks
    cleaned = text.replace("<br>", "\n\n").replace("<br/>", "\n\n").replace("<br />", "\n\n")
    return cleaned

def clean_rubbish_formatting(text: str) -> str:
    """Removes raw Markdown symbols so the user can edit clean text."""
    if not text:
        return ""
    
    # 1. Convert markdown dashes/asterisks at start of lines to clean Unicode bullets
    text = re.sub(r'^[\-\*]\s+', '• ', text, flags=re.MULTILINE)
    
    # 2. Remove all bold/italic asterisks and underscores (**text** -> text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    
    # 3. Remove header hashes (### Heading -> Heading)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # 4. Remove table pipes
    text = text.replace('|', '  ')
    
    return text
# --------------------------------------------------

load_dotenv()
init_db()

st.set_page_config(page_title="Career Platform", layout="wide")
st.title("🎯 Career Platform")

if "phase1_pipe" not in st.session_state:
    st.session_state.phase1_pipe = build_phase1_pipeline()
if "phase2_pipe" not in st.session_state:
    st.session_state.phase2_pipe = build_phase2_pipeline()
if "phase3_pipe" not in st.session_state:
    st.session_state.phase3_pipe = build_phase3_pipeline()

    
# --- PHASE 1 SECTION ---
st.header("Upload Resume & Analyse Skills")
# 1. Update file_uploader to accept both pdf and docx
uploaded_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])

if uploaded_file:
    # 2. File Type Extension Check
    file_name = uploaded_file.name.lower()
    if not (file_name.endswith(".pdf") or file_name.endswith(".docx")):
        st.warning("⚠️ Unsupported file format! Please upload a valid PDF or DOCX file.")
    else:
        if st.button("Process Resume"):
            with st.spinner("Agent 1 (Resume Parser) & Agent 2 (Resume Analyzer) working..."):

                # Clear previous state on fresh upload
                keys_to_clear = [
                    "resume_processed",
                    "current_state",
                    "raw_job_listings",
                    "parsed_jobs",
                    "match_results",
                    "selected_role",
                    "career_report",
                    "p2_complete",
                    "p3_complete",
                    "market_report"
                ]
                for key in keys_to_clear:
                    st.session_state.pop(key, None)

                # 3. Use generic file extraction logic instead of extract_text_from_pdf
                raw_text = extract_text_from_file(uploaded_file)
                
                # 4. Check for empty/unreadable text
                if not raw_text or not raw_text.strip():
                    st.error("⚠️ The uploaded file appears to be empty or unreadable text. Please upload a standard text-based PDF or DOCX resume.")
                else:
                    resume_id = save_initial_resume(uploaded_file.name, raw_text)
                    
                    initial_state = {
                        "resume_id": resume_id,
                        "file_name": uploaded_file.name,
                        "resume_text": raw_text,
                        "parsed_skills": [],
                        "parsed_certifications": [],
                        "candidate_experience": "",
                        "candidate_years": 0.0,
                        "recommended_roles": [],
                        "selected_role": None,
                        "selected_location": "India",
                        "raw_job_listings": [],
                        "parsed_jobs": []
                    }
                   
                    final_p1_state = st.session_state.phase1_pipe.invoke(initial_state)
                    
                    # 5. Document Validity Guardrail Check
                    is_valid = final_p1_state.get("is_valid_resume", True)
                    validation_reason = final_p1_state.get("validation_reason", "Invalid document structure.")

                    if not is_valid:
                        st.error(f"❌ **Invalid Resume Document:** {validation_reason}")
                        st.info("💡 Please upload a valid, professional resume to extract skills and view role recommendations.")
                    else:
                        # Fallback Handling for missing fields on valid resumes
                        extracted_skills = final_p1_state.get("parsed_skills") or ["None"]
                        extracted_certs = final_p1_state.get("parsed_certifications") or ["None"]
                        extracted_exp = final_p1_state.get("candidate_experience", "").strip() or "None"
                        recommended_roles = final_p1_state.get("recommended_roles") or ["Software Engineer"]

                        # Update normalized fields in final state
                        final_p1_state["parsed_skills"] = extracted_skills
                        final_p1_state["parsed_certifications"] = extracted_certs
                        final_p1_state["candidate_experience"] = extracted_exp
                        final_p1_state["recommended_roles"] = recommended_roles

                        # Persist normalized values to database
                        update_resume_analysis(
                            resume_id=resume_id,
                            skills=extracted_skills,
                            certifications=extracted_certs,
                            experience=extracted_exp,
                            roles=recommended_roles
                        )
                        
                        st.session_state.current_state = final_p1_state
                        st.session_state.resume_processed = True           
                        st.rerun()
                        
# --- PHASE 2 SECTION ---
if st.session_state.get("resume_processed"):
    state = st.session_state.current_state
    
    # Safe Fallback Formatting
    parsed_skills = state.get("parsed_skills", [])
    skills_display = ", ".join(parsed_skills) if parsed_skills else "None"
    
    parsed_certs = state.get("parsed_certifications", [])
    certs_display = ", ".join(parsed_certs) if parsed_certs else "None"
    
    exp_summary = str(state.get("candidate_experience", "")).strip()
    exp_display = exp_summary if exp_summary else "None"

    rec_roles = state.get("recommended_roles", [])
    roles_display = ", ".join(rec_roles) if rec_roles else "Software Engineer"

    st.divider()
    st.subheader("Candidate Analysis Summary")
    st.write(f"**Extracted Skills:** {skills_display}")
    st.write(f"**Extracted Certifications:** {certs_display}")
    st.write(f"**Years of Experience:** `{state.get('candidate_years', 0.0)} years`")
    st.write(f"**Experience Summary:** {exp_display}")
    st.write(f"**Recommended Roles:** {roles_display}")
    
    st.divider()
    st.subheader("Select Target Role & Location for Job Search")
    
    # Role and Location Dropdowns
    col1, col2 = st.columns(2)
    with col1:
        selected_role = st.selectbox(
            "Select Target Role:", 
            options=rec_roles if rec_roles else [" None Available "],
            index=0
        )
    with col2:
        selected_location = st.selectbox(
            "Select Location in India:", 
            options=["India", "Bengaluru", "Hyderabad", "Mumbai", "Pune", "Delhi NCR", "Chennai", "Kolkata", "Gurgaon", "Noida"],
            index=0
        )
    
    # Action Row: Search Button + Filter Checkbox side-by-side
    btn_col, chk_col = st.columns([1, 2])
    
    with btn_col:
        search_clicked = st.button("Search & Parse Jobs")
        
    with chk_col:
        hide_below_exp = st.checkbox(
            "Hide jobs far below my experience level",
            value=st.session_state.get("hide_below_exp", False),
            help="Filter out entry-level roles when you have higher candidate experience."
        )
        st.session_state["hide_below_exp"] = hide_below_exp

    # Trigger Search Flow
    if search_clicked:
        with st.spinner("Agent 3 (Job Search) & Agent 4 (Job Parser) working..."):
            state["selected_role"] = selected_role
            state["selected_location"] = selected_location
            state["hide_below_exp"] = hide_below_exp
            
            final_p2_state = st.session_state.phase2_pipe.invoke(state)
            
            # Filter jobs if checkbox is checked
            if hide_below_exp:
                cand_years = state.get("candidate_years", 0.0)
                all_jobs = final_p2_state.get("parsed_jobs", [])
                filtered = [
                    j for j in all_jobs 
                    if not (cand_years >= 3.0 and j.get("required_years_experience", 0.0) <= 0.5)
                ]
                final_p2_state["parsed_jobs"] = filtered

            # Save parsed job data to DB
            save_parsed_jobs(
                resume_id=final_p2_state["resume_id"],
                selected_role=selected_role,
                parsed_jobs=final_p2_state.get("parsed_jobs", [])
            )
            
            st.session_state.current_state = final_p2_state
            st.session_state.p2_complete = True
            st.rerun()

if st.session_state.get("p2_complete"):
    st.divider()
    st.subheader("📋 Parsed Job Descriptions")
    
    parsed_jobs = st.session_state.current_state.get("parsed_jobs", [])
    cand_years = float(st.session_state.current_state.get("candidate_years", 0.0))
    
    # Ensure items are strictly sorted descending by overall match score
    sorted_jobs = sorted(parsed_jobs, key=lambda x: x.get("match_score", 0), reverse=True)
    
    for idx, job in enumerate(sorted_jobs, 1):
        score = job.get("match_score", 0.0)
        eval_res = job.get("evaluation", {})
        
        expand_title = f"Rank #{idx} | {score}% Composite Match — 🏢 {job['company']} — {job['title']} ({job['location']})"
        
        with st.expander(expand_title, expanded=(idx == 1)):
            eval_res = job.get("evaluation", {})
            cert_score_val = eval_res.get("certification_score")

            # Format metric value: display 'N/A' if None, otherwise format as percentage
            cert_metric_str = "N/A" if cert_score_val is None else f"{cert_score_val}%"
            # Score Breakdown Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Overall Fit", f"{score}%")
            m2.metric("Skill Match (60%)", f"{eval_res.get('skill_score', score)}%")
            m3.metric("Exp Fit (30%)", f"{eval_res.get('experience_score', 100.0)}%")
            m4.metric("Cert Fit (10%)", cert_metric_str)

            st.progress(score / 100.0)

            # Display Warnings (Under/Over-qualification)
            warnings = eval_res.get("warnings", [])
            for warn in warnings:
                st.warning(warn)

            matched = eval_res.get("matched_skills", [])
            missing = eval_res.get("missing_skills", [])

            col1, col2 = st.columns(2)
            with col1:
                st.write("**✅ Skills You Have:**", ", ".join([f"`{s}`" for s in matched]) or "_None_")
            with col2:
                if not matched and not missing:
                    st.write("**❌ Missing Skills:**", "_No explicit skills listed in JD_")
                else:
                    st.write("**❌ Missing Skills:**", ", ".join([f"`{s}`" for s in missing]) or "_None_")    
            
            # Certifications Breakdown
            req_certs = eval_res.get("required_certs", job.get("required_certifications", []))
            if not req_certs:
                st.caption("📜 **Certifications:** _Not required for this role_")
            else:
                matched_certs = [c for c in st.session_state.current_state.get("parsed_certifications", []) if c in req_certs]
                missing_certs = [c for c in req_certs if c not in matched_certs]
                st.write("**📜 Required Certifications:**", ", ".join([f"`{c}`" for c in req_certs]))
                if missing_certs:
                    st.caption(f"⚠️ Missing required certifications: {', '.join(missing_certs)}")

            # Experience Requirement Display 
            req_years = job.get("required_years_experience", eval_res.get("required_years", 0.0))
            cand_years = st.session_state.current_state.get("candidate_years", 0.0)

            if req_years == 0.0:
                st.markdown("⏳ **Required Experience:** `Entry Level / Not Specified`")
            else:
                st.markdown(f"⏳ **Required Experience:** `{req_years} years` _(Your Experience: {cand_years} years)_")

            # Raw Description Excerpt
            st.caption(f"**Raw Description Excerpt:** {job.get('description', '')[:300]}...")    

# --- PHASE 3: SKILL GAP & MATCH ANALYSIS ---
if st.session_state.get("p2_complete"):
    st.divider()
    st.header("⚡ Skill Gap Analysis ")
    
    if st.button("Run Skill Gap Analysis"):
        with st.spinner("Agent 5 (Skill Gap & Match Agent) analyzing ..."):
            state = st.session_state.current_state
            final_p3_state = st.session_state.phase3_pipe.invoke(state)
            
            # Save results to DB
            save_match_results(
                resume_id=final_p3_state["resume_id"],
                match_results=final_p3_state["match_results"]
            )
            
            st.session_state.current_state = final_p3_state
            st.session_state.p3_complete = True
            st.rerun()

if st.session_state.get("p3_complete"):
    st.divider()
    st.subheader("📋 Parsed Skills ")
    
    state = st.session_state.current_state
    match_results = state.get("match_results", [])
    cand_years = float(state.get("candidate_years", 0.0))
    hide_below_exp = st.session_state.get("hide_below_exp", False)
    
    # 1. Apply filter if toggled
    if hide_below_exp:
        match_results = [
            j for j in match_results 
            if (cand_years - float(j.get("required_years_experience", 0.0))) <= 4.0
        ]

    # 2. Filter out 0% matches and sort in descending priority
    top_matched_jobs = [j for j in match_results if j.get("match_score", 0) > 0]
    top_matched_jobs = sorted(top_matched_jobs, key=lambda x: x.get("match_score", 0), reverse=True)
    
    if not top_matched_jobs:
        st.warning("No high-matching job roles found for your criteria. Try adjusting target locations or expanding your resume skills.")
    else:
        # === START OF LOOP ===
        for idx, res in enumerate(top_matched_jobs, 1):
            with st.container():
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"### Rank #{idx}: {res.get('job_title', 'Role')} at {res.get('company', 'Company')}")
                with col_b:
                    st.metric("Skills Matching Score", f"{res.get('match_score', 0)}%")
                
                # Visual Progress Bar
                st.progress(res.get('match_score', 0) / 100.0)
                
                # Render Warnings if present
                eval_info = res.get("evaluation", {})
                for warning in eval_info.get("warnings", []):
                    st.warning(warning)
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.write("**✅ Matched Skills:**", ", ".join([f"`{s}`" for s in res.get('matched_skills', [])]) or "_None_")
                with col_m2:
                    st.write("**❌ Missing Skills:**", ", ".join([f"`{s}`" for s in res.get('missing_skills', [])]) or "_None_")
                
                # Clean HTML tags (<br>) from LLM output before displaying
                cleaned_recommendation = clean_markdown_output(res.get('recommendation', ''))
                
                # Collapsible Expander for Actionable Recommendations
                with st.expander("💡 View Actionable Recommendations & Guidance", expanded=False):
                    st.markdown(cleaned_recommendation)

                # --- TAILORED RESUME GENERATION & EDITING (MUST BE INDENTED INSIDE LOOP) ---
                if st.button(f"📄 Generate Tailored Resume for {res.get('company', 'Company')}", key=f"gen_res_{idx}"):
                    with st.spinner(f"Generating optimized resume structure for {res.get('job_title', 'Role')}..."):
                        
                        default_html = generate_resume_html(
                            name="SOUVIK GHOSH",
                            title=f"{res.get('job_title', 'Backend Engineer')}",
                            phone="+91 967 484 7794",
                            email="souvik.ghosh12@tcs.com",
                            github="https://github.com",
                            linkedin="https://linkedin.com",
                            education="<b>B.Tech, Computer Science & Engineering</b> — St. Thomas' College of Engineering & Technology (2020-2024) | <b>CGPA: 9.0/10</b>",
                            summary="Seasoned Backend Engineer with experience designing and delivering secure, high-performance microservice ecosystems. Expert in RESTful APIs, modernizing legacy platforms, and driving CI/CD automation.",
                            competencies={
                                "Languages": "Java, Python, SQL, PL/SQL",
                                "Frameworks & APIs": "Spring Boot, Spring MVC, Spring Security, Spring Data JPA, Hibernate, REST/GraphQL",
                                "Architecture": "Microservices, Event-driven (Kafka), Serverless, Scalable Systems",
                                "Databases & Storage": "MySQL, PostgreSQL, MongoDB, Redis, Cloud SQL, S3",
                                "Cloud & DevOps": "AWS (ECS, RDS, S3, Lambda), GCP, Docker, Kubernetes, GitHub Actions, Terraform"
                            },
                            experiences=[
                                {
                                    "company": "Tata Consultancy Services (TCS)",
                                    "role": "Backend Engineer",
                                    "location": "Hybrid",
                                    "dates": "May 2025 - Present",
                                    "bullets": [
                                        "Modernized high-volume payment platform: Re-architected legacy payment rail into cloud-native microservice suite (12 services) using Spring Boot, Docker, and AWS ECS.",
                                        "Designed secure RESTful APIs with JWT/OAuth2 and Swagger, achieving 99.99% SLA.",
                                        "Automated CI/CD pipelines with GitHub Actions, Terraform, and Helm, reducing release cycles from 2 weeks to 2 days."
                                    ]
                                },
                                {
                                    "company": "Zediant Technologies",
                                    "role": "Intern / Backend Engineer",
                                    "location": "Hybrid",
                                    "dates": "Feb 2024 - May 2025",
                                    "bullets": [
                                        "Built REST APIs for SaaS subscription products handling 500k+ active users.",
                                        "Optimized complex SQL queries, delivering a 60% reduction in response time."
                                    ]
                                }
                            ],
                            projects=[
                                {
                                    "name": "ShopEase Platform",
                                    "tech": "Spring Boot, Kafka, Redis, AWS S3",
                                    "impact": "Delivered fault-tolerant system handling 10k+ concurrent users with sub-second response time."
                                }
                            ],
                            certifications=[
                                "AWS Certified Solutions Architect - Associate (2024)",
                                "Google Cloud Professional Cloud Developer (2023)",
                                "Top ranked AIR 248 in All India Coding Contest (2023)"
                            ]
                        )
                        st.session_state[f"tailored_html_{idx}"] = default_html

                # EDITABLE PREVIEW & DOWNLOAD (SIDE-BY-SIDE LAYOUT)
                if f"tailored_html_{idx}" in st.session_state:
                    st.markdown("#### 🛠️ Edit & Preview Tailored Resume")
                    st.caption("Edit the HTML structure on the left to see instant visual updates on the right. Downloads will compile your live changes.")
                    
                    # Create 2 side-by-side equal width columns
                    col_editor, col_preview = st.columns(2)
                    
                    with col_editor:
                        st.markdown("**Raw HTML Code Editor**")
                        edited_html = st.text_area(
                            label=f"Edit Resume HTML ({res.get('company', '')}):",
                            value=st.session_state[f"tailored_html_{idx}"],
                            height=650,
                            key=f"html_editor_{idx}",
                            label_visibility="collapsed"
                        )
                        # Save latest edits directly back to session state
                        st.session_state[f"tailored_html_{idx}"] = edited_html

                    with col_preview:
                        st.markdown("**Live Visual Resume Preview**")
                        # Render live styled HTML preview in browser frame
                        st.components.v1.html(edited_html, height=650, scrolling=True)

                    # Generate PDF bytes dynamically from the EXACT EDITED HTML string
                    resume_pdf = generate_pdf_bytes_from_html(edited_html)
                    
                    st.download_button(
                        label=f"⬇️ Download Tailored Resume ({res.get('company', 'Company')}.pdf)",
                        data=resume_pdf,
                        file_name=f"Tailored_Resume_{res.get('company', 'Company')}.pdf",
                        mime="application/pdf",
                        key=f"dl_res_{idx}"
                    )
                st.divider()
        # === END OF LOOP ===

# --- FINAL MARKET RADAR & FUTURE REPORT ---

# Wrap the Market Report so it only appears AFTER skill gap analysis completes
if st.session_state.get("p3_complete"):
    st.divider()
    st.header("📈 Final Career & Market Analysis Report")

    if st.button("Generate Full Market Analysis Report"):
        with st.spinner("Generating Market Intelligence Report..."):
            market_report = generate_market_report(
                skills=state.get("parsed_skills", []),
                experience=state.get("candidate_experience", ""),
                target_role=state.get("selected_role", "Software Engineer")
            )
            save_market_report(state["resume_id"], market_report)
            st.session_state.market_report = market_report

    if "market_report" in st.session_state:
        report = st.session_state.market_report
        st.markdown(report)
        
        report_pdf = generate_pdf_bytes(
            title="Career & Market Analysis Report",
            text_content=report
        )
        #download button for the market report PDF
        # st.download_button(
        #     label="⬇️ Download Market Analysis Report (.pdf)",
        #     data=report_pdf,
        #     file_name=f"Career_Market_Report_{state['resume_id']}.pdf",
        #     mime="application/pdf",
        #     key="dl_market_report"
        # )