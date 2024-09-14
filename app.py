from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# API keys for Spoonacular (Recipes) and Yelp (Restaurants)
SPOONACULAR_API_KEY = 'your_spoonacular_api_key'
YELP_API_KEY = 'your_yelp_api_key'

# Home route to display input form
@app.route('/')
def home():
    return render_template('index.html')

# Route to process user input and return recommendations
@app.route('/recommend', methods=['POST'])
def recommend():
    calorie_intake = int(request.form['calories'])
    dietary_restrictions = request.form.getlist('restrictions')
    dietary_preferences = request.form['preferences']
    meals_per_day = int(request.form['meals'])

    # Calculate calories per meal
    calories_per_meal = calorie_intake // meals_per_day

    # Fetch recipe recommendations
    recipe_results = get_recipe_recommendations(calories_per_meal, dietary_restrictions, dietary_preferences)

    # Fetch restaurant recommendations
    location = 'your_location'  # Can be dynamic, based on user input
    restaurant_results = get_restaurant_recommendations(dietary_preferences, dietary_restrictions, location)

    return render_template('results.html', recipes=recipe_results, restaurants=restaurant_results)

def get_recipe_recommendations(calories_per_meal, restrictions, preferences):
    url = f"https://api.spoonacular.com/recipes/complexSearch?apiKey={SPOONACULAR_API_KEY}"
    params = {
        'maxCalories': calories_per_meal,
        'diet': preferences,  # E.g., 'vegetarian'
        'intolerances': ','.join(restrictions),  # E.g., 'gluten, dairy'
        'number': 5
    }
    response = requests.get(url, params=params)
    return response.json().get('results', [])

def get_restaurant_recommendations(preferences, restrictions, location):
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {
        'term': preferences,  # E.g., 'vegan', 'Japanese'
        'location': location,
        'categories': ','.join(restrictions),  # E.g., 'gluten-free'
        'limit': 5
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json().get('businesses', [])

if __name__ == '__main__':
    app.run(debug=True)
