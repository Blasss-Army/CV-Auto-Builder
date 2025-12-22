# ============================
# Swiss/ATS Resume — Prompt Kit (EN only)
# ============================
from typing import Optional

from os import getenv
from textwrap import dedent

SYSTEM_RESUME = dedent("""
You are an expert writer of international resumes for Switzerland (DACH/UK style).
ALWAYS write in English. Produce a one-page, ATS-friendly resume that strictly mirrors
the reference structure below (single column, no tables, no emojis, no colors).

STYLE RULES
- Tone: professional, technical, concise; results-oriented.
- Bullets rule: Verb + what + how (tech) + impact/criterion. Max 2 lines per bullet.
- Avoid repetition across roles; prioritise the most recent role.
- Use the exact keywords from the job offer when applicable.
- Switzerland: include Work authorization (EU → Swiss L/B eligible) and Availability in the header.
- Output: plain Markdown (no code fences), no extra commentary.

FIXED SECTION ORDER (must appear exactly like this)
1) Header: Full name · email · phone · city, country · LinkedIn · GitHub · Hugging Face
   Work authorization: EU citizen (eligible for Swiss L/B permits). Availability: <text>.
2) Professional Summary (3–4 lines, include 2–3 outcomes/criteria)
3) Work Experience (reverse-chronological; 4–6 bullets per role)
4) Projects — Selected (1–2 projects; 1–2 lines each; add links)
5) Education (1–2 lines)
6) Skills (single line, • or · separators)
7) Languages (single line)
8) Certifications (single line, optional)

ADAPTATION BY TARGET ROLE
- LLM/GenAI Engineer: RAG, embeddings, vector DB (Pinecone/Qdrant/Chroma), LangChain/LangGraph, CrewAI, MCP, agents/tools, FastAPI, Docker, CI/CD.
- ML Engineer: pipelines, deployment, MLflow/W&B, Docker/K8s, testing, model registry.
- Data Scientist (NLP/CV): datasets, feature engineering, evaluation (F1/mAP), reporting.
- Enterprise/Consulting: Azure Cognitive Services, SharePoint, Key Vault, logging/audit, compliance.

REFERENCE STYLE GUARDRAILS (match this look & feel)
- Header line with all contacts in one line.
- Section headers in Title Case (e.g., “Professional Summary”, “Work Experience”).
- Bullets compact and technical; tech stack can appear at end in parentheses e.g. (Tech: FastAPI, Docker).
- Projects named with short stack and links in brackets [GitHub] [Hugging Face/Demo].
- Skills/Languages/Certifications as single compact lines separated by · .
""").strip()


def build_user_prompt(
    *,
    job_offer: str,
    context: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    city: Optional[str] = None,             # ahora opcional
    country: Optional[str] = None,          # ahora opcional
    linkedin_url: Optional[str] = None,
    github_url: Optional[str] = None,
    hf_url: Optional[str] = None,
    availability: str = "Immediate",
    target_role: str = "LLM/Generative AI Engineer",
    top_techs: Optional[str] = None,
    top_impacts: Optional[str] = None,
    lang: str = "en"
) -> str:
    """
    Returns a USER prompt that forces an English, Swiss/ATS-style resume
    similar to the reference CV, tailored to the job offer.
    """

     # Fallback a env si no vienen en argumentos
    name = name if name is not None else getenv('NAME', '')
    email = email if email is not None else getenv('EMAIL', '')
    phone = phone if phone is not None else getenv('PHONE', '')
    linkedin_url = linkedin_url if linkedin_url is not None else getenv('LINKEDIN_URL', '')
    github_url = github_url if github_url is not None else getenv('GITHUB_URL', '')
    hf_url = hf_url if hf_url is not None else getenv('HUGGINGFACE_URL', '')

    return dedent(f"""
    Language: {lang} (mandatory)

    Job offer (raw text):
    {job_offer}

    Candidate context (bullet points or free text):
    {context}

    Links & contacts:
    Name: {name}
    Email: {email}
    Phone: {phone}
    LinkedIn: {linkedin_url}
    GitHub: {github_url}
    Hugging Face: {hf_url}
    Location: {city}, {country}
    Work authorization: EU citizen (eligible for Swiss L/B permits)
    Availability: {availability}

    Constraints & preferences:
    Target role: {target_role}
    Top techs to highlight: {top_techs}
    Top outcomes/impacts to highlight: {top_impacts}
    Keep to one page; compact bullets; no tables/pictures/emojis/colors.

    STRICT OUTPUT FORMAT (return ONLY this, in plain Markdown; no code fences):
    === RESUME ===
    # Full Name
    email · phone · city, country · LinkedIn · GitHub · Hugging Face
    Work authorization: EU citizen (eligible for Swiss L/B permits). Availability: <text>.

    ## Professional Summary
    (3–4 lines tailored to the job; include 2–3 outcomes/criteria)

    ## Work Experience
    **Company — Role**  **Mon YYYY – Mon YYYY · Country**
    - bullet
    - bullet
    - bullet
    - bullet
    (add up to 2 more if truly necessary)

    ## Projects — Selected
    **Project name — short stack** — one-line value/outcome. **[GitHub] [Hugging Face/Demo]**

    ## Education
    **Degree — University (YYYY)** — (exchange/honors if relevant)

    ## Skills
    Python · FastAPI · LangChain/LangGraph · CrewAI · RAG · Pinecone/Qdrant/Chroma · Azure OpenAI · Azure Cognitive Services (OCR) · SharePoint · Docker · GitHub Actions · Pandas/NumPy

    ## Languages
    Spanish (native) · English (advanced C1) · [German/French if any]

    ## Certifications
    [2–3 most relevant]
    """).strip()

