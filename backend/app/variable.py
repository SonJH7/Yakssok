import os
from dotenv import load_dotenv


load_dotenv()


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

FRONTEND_URL = os.getenv("FRONTEND_URL", "localhost:5173")
