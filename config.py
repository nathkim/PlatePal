from dotenv import load_dotenv
import os

load_dotenv() 

SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY')

if not SPOONACULAR_API_KEY:
    raise ValueError("No SPOONACULAR_API_KEY set for Flask application.")

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not SPOONACULAR_API_KEY:
    raise ValueError("No OPENAI_API_KEY set for Flask application.")