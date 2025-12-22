# w3global_search.py
from urllib.parse import urlencode, quote_plus

def build_w3global_jobs_url(
    keyword: str | None = None,
    location: str | None = None,
) -> str:
    base = "https://www.w3global.com/search-jobs"
    params: dict[str, str] = {}

    if keyword:
        params["keyword"] = keyword


    if location:
        params["location"] = location

    return base + ("?" + urlencode(params, quote_via=quote_plus) if params else "")


print(build_w3global_jobs_url(keyword="data scientist", location="Remote"))