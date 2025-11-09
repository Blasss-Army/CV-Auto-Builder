# linkedin_search.py

from urllib.parse import urlencode, quote_plus

# Mapeos no oficiales; LinkedIn puede cambiarlos. Sirven para búsquedas básicas.
WORK_TYPE = {"on-site": "1", "remote": "2", "hybrid": "3"}        # f_WT
EXP = {
    "internship": "1", "entry": "2", "associate": "3",
    "mid-senior": "4", "director": "5", "executive": "6"          # f_E
}
POSTED = {"24h": "r86400", "week": "r604800", "month": "r2592000"}  # f_TPR

def build_linkedin_jobs_url(
    keywords: str,
    location: str | None = None,
    work_types: list[str] | None = None,
    experience: list[str] | None = None,
    posted: str | None = None,
    easy_apply: bool = False,          # << nuevo
    actively_hiring: bool = True,     # << opcional
    sort_newest: bool = True           # << opcional
) -> str:
    
    params: dict[str, str] = {}

    if keywords: 
        params["keywords"] = keywords

    if location:
        params["location"] = location

    if work_types:
        codes = [WORK_TYPE[w] for w in work_types if w in WORK_TYPE]
        if codes: params["f_WT"] = ",".join(codes)

    if experience:
        codes = [EXP[e] for e in experience if e in EXP]
        if codes: params["f_E"] = ",".join(codes)

    if posted and posted in POSTED:
        params["f_TPR"] = POSTED[posted]

     # --- filtros no oficiales ---
    if easy_apply:
        params["f_EA"] = "true"        # Empresas con “Actively Hiring”.
    if actively_hiring:
        params["f_AL"] = "true"        # Solo Easy Apply (no documentado). 
    if sort_newest:
        params["sortBy"] = "DD"        # Newest first.
        
    base = "https://www.linkedin.com/jobs/search/"

    return base + "?" + urlencode(params, quote_via=quote_plus)
