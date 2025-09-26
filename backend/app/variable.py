import os
from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse


load_dotenv()

_ALLOWED_FRONTEND_SCHEMES = {"http", "https"}


def _normalize_frontend_url(url: str) -> str:
    if not url:
        return url

    stripped = url.strip()

    if not stripped:
        return stripped

    def _rebuild(parsed_url, default_scheme: str = "http") -> str:
        scheme = parsed_url.scheme.lower() if parsed_url.scheme else default_scheme
        netloc = parsed_url.netloc
        path = parsed_url.path

        if not netloc and path:
            segments = path.split("/", 1)
            netloc = segments[0]
            path = f"/{segments[1]}" if len(segments) == 2 else ""

        return urlunparse((scheme, netloc, path, "", "", ""))

    if stripped.startswith("//"):
        parsed = urlparse(f"http:{stripped}")
        return _rebuild(parsed)

    if "://" not in stripped:
        parsed = urlparse(f"http://{stripped}")
        return _rebuild(parsed)

    parsed = urlparse(stripped)

    if (
        parsed.scheme
        and parsed.netloc
        and parsed.scheme.lower() in _ALLOWED_FRONTEND_SCHEMES
    ):
        return _rebuild(parsed, parsed.scheme.lower())

    remainder = stripped.split("://", 1)[1]
    parsed = urlparse(f"http://{remainder}")

    return _rebuild(parsed)


SQLALCHEMY_DATABASE_URL_USER = os.environ.get("SQLALCHEMY_DATABASE_URL_USER")
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", "86400")
)


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_FORCE_PROMPT_CONSENT = (
    os.getenv("GOOGLE_FORCE_PROMPT_CONSENT", "false").lower() == "true"
)

FRONTEND_URL = _normalize_frontend_url(
    os.getenv("FRONTEND_URL", "http://localhost:5173")
)
