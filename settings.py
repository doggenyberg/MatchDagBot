import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_API_SECRET = os.getenv('DISCORD_API_SECRET')
FOOTBALL_API_SECRET = os.getenv('FOOTBALL_API_SECRET')