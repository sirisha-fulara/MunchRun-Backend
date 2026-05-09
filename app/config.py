import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI= os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS= False
    JWT_SECRET_KEY= os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES=3600 #after 1 hr
    JWT_REFRESH_TOKEN_EXPIRES=2592000 #after 30 days