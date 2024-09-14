from flask import Flask, render_template, request
import requests, os, openai
from config import SPOONACULAR_API_KEY, OPENAI_API_KEY

app = Flask(__name__)

# Home route to display input form
@app.route('/')
def home():
    return render_template('index.html')

# Route to process user input and return recipe search results
@app.route('/recommend', methods=['POST'])
def recommend():
    calorie_intake = int(request.form['calories'])
    dietary_restrictions = request.form.getlist('restrictions')
    dietary_preferences = request.form['preferences']
    meals_per_day = int(request.form['meals'])

    # Calculate calories per meal
    calories_per_meal = calorie_intake // meals_per_day

    # Fetch recipe recommendations
    recipes = get_recipe_recommendations(calories_per_meal, dietary_restrictions, dietary_preferences)

    return render_template('results.html', recipes=recipes)

# Route to display detailed recipe information
@app.route('/recipe/<int:recipe_id>')
def recipe_info(recipe_id):
    recipe_details = get_recipe_information(recipe_id)
    return render_template('recipe_info.html', recipe=recipe_details)

# Route to test if the Spoonacular API works
@app.route('/test-api')
def test_api():
    test_url = f"https://api.spoonacular.com/recipes/complexSearch?apiKey={SPOONACULAR_API_KEY}&query=salad&number=1"
    response = requests.get(test_url)
    
    if response.status_code == 200:
        return f"API Test Successful: {response.json()}"
    else:
        return f"API Test Failed: {response.status_code}"

# Function to search for recipes
def get_recipe_recommendations(calories_per_meal, restrictions, preferences, number_of_recipes=5):
    url = f"https://api.spoonacular.com/recipes/complexSearch"
    params = {
        'apiKey': SPOONACULAR_API_KEY,
        'maxCalories': calories_per_meal,
        'diet': preferences,
        'intolerances': ','.join(restrictions),
        'number': number_of_recipes
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        print(f"Error: {response.status_code}")
        return []

# Function to get detailed recipe information
def get_recipe_information(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {
        'apiKey': SPOONACULAR_API_KEY
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return {}

if __name__ == '__main__':
    app.run(debug=True)