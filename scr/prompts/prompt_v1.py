'''
user = (
        f"You are an expert in writing resumes. Language: {lang}.\n"
        f"Job offer:\n{job_offer}\n\nCandidate context (bullet points):\n{context}\n\n"
        "Write a short (120–180 words) cover letter highly tailored to the offer, "
        "Next you will receive some relevant information about the candidate. Use it to make the resume more personalized and specific." \
        f"Name > {os.getenv("NAME","")}, Email > {os.getenv("EMAIL","")}, Phone > {os.getenv("PHONE","")}, " \
        f"GitHub > {os.getenv("GITHUB_URL","")}, HuggingFace > {os.getenv("HUGGINGFACE_URL","")}, LinkedIn > {os.getenv("LINKEDIN_URL","")}.\n\n" \
        
        "The resume should be structured"
        "First sentence with all mentioned candidate info. "
        "with a professional tone, mentioning 2–3 quantified achievements, and a clear closing."
        "Start immediately with the 'Summary' section.\n"
        "IMPORTANT >>> Do NOT use code fences (```), return plain Markdown.\n"  
    )
'''

# prompts.py
from os import getenv
from textwrap import dedent

def build_resume_prompt(lang: str, job_offer: str, context: str) -> str:
    """
    Construye la prompt para generar (1) cover letter y (2) resume en Markdown.
    - lang: idioma de salida (p.ej., 'English', 'Spanish').
    - job_offer: texto de la oferta.
    - context: bullet points del candidato (puede ser multilinea con '- ').
    """
    name = getenv('NAME', '')
    email = getenv('EMAIL', '')
    phone = getenv('PHONE', '')
    github = getenv('GITHUB_URL', '')
    hf = getenv('HUGGINGFACE_URL', '')
    linkedin = getenv('LINKEDIN_URL', '')

    contact_line = (
        f"Name > {name}, Email > {email}, Phone > {phone}, "
        f"GitHub > {github}, HuggingFace > {hf}, LinkedIn > {linkedin}."
    )

    # Nota: usamos dedent + triple comillas para evitar problemas de comillas y barras
    prompt = dedent(f"""
        You are an expert in writing resumes. Language: {lang}.

        Job offer:
        {job_offer}

        Candidate context (bullet points):
        {context}

        Produce two sections in plain Markdown (no code fences):
        1) Cover Letter (120–180 words), highly tailored to the offer, professional tone.
        2) Resume starting with a 'Summary' section, followed by key skills and experience.
           Mention 2–3 quantified achievements and include a clear closing.

        Use the following candidate info to personalize the content:
        {contact_line}

        IMPORTANT >>> Do NOT use code fences (```); return plain Markdown only.
    """).strip()

    return prompt