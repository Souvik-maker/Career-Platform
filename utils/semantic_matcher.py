from sentence_transformers import SentenceTransformer, util

# Model for semantic matching of skills
model = SentenceTransformer('all-MiniLM-L6-v2')

def calculate_semantic_match(candidate_skills: list, job_required_skills: list, threshold: float = 0.65):
    """
    Compares candidate vectors against job requirement vectors.
    Returns calculated match percentage, matched requirements, and true missing requirements.
    """
    # Ensure inputs are standard Python lists
    cand_list = list(candidate_skills) if isinstance(candidate_skills, (set, tuple)) else candidate_skills
    job_list = list(job_required_skills) if isinstance(job_required_skills, (set, tuple)) else job_required_skills

    if not job_list:
        return 0.0, [], []
        
    if not cand_list:
        return 0.0, [], job_list

    # sentence-transformers model encodes the skills into vector representations
    cand_vectors = model.encode(cand_list, convert_to_tensor=True)
    job_vectors = model.encode(job_list, convert_to_tensor=True)
    # here we compute the cosine similarity between each job skill vector and candidate skill vectors
    similarity_matrix = util.cos_sim(job_vectors, cand_vectors)

    matched_skills = []
    missing_skills = []

    for i, req_skill in enumerate(job_list):
        max_score = float(similarity_matrix[i].max())
        if max_score >= threshold:
            matched_skills.append(req_skill)
        else:
            missing_skills.append(req_skill)

    match_percentage = round((len(matched_skills) / len(job_list)) * 100, 1)
    return match_percentage, matched_skills, missing_skills