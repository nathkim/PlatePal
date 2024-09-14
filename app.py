from flask import Flask, render_template, request, session, redirect, url_for
import requests
from config import SPOONACULAR_API_KEY

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

# Home route to display input form
@app.route('/')
def home():
    return render_template('index.html')

# Route to process user input and return recipe search results
@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        calorie_intake = int(request.form.get('calories', 0))
        dietary_restrictions = request.form.getlist('allergies')  # Updated from 'restrictions'
        dietary_preferences = request.form.getlist('preferences')  # Updated to use getlist for multiple values
        meals_per_day = int(request.form.get('meals', 1))  # Default to 1 if not provided

        if meals_per_day <= 0:
            meals_per_day = 1  # Prevent division by zero

        # Calculate calories per meal
        calories_per_meal = calorie_intake // meals_per_day

        # Fetch recipe recommendations
        recipes = get_recipe_recommendations(calories_per_meal, dietary_restrictions, dietary_preferences)

        return render_template('results.html', recipes=recipes)
    except ValueError:
        # Handle value errors in case of invalid integer conversions
        return "Invalid input. Please check your values and try again."

# Route to handle saving liked recipes
@app.route('/save-likes', methods=['POST'])
def save_likes():
    liked_recipe_ids = request.form.getlist('liked_recipes')
    
    if 'liked_recipes' not in session:
        session['liked_recipes'] = []

    # Update session liked recipes list based on the checkboxes
    current_likes = set(session['liked_recipes'])
    new_likes = set(liked_recipe_ids)
    
    # Add new likes and remove unliked recipes
    session['liked_recipes'] = list(current_likes.union(new_likes))
    
    return redirect(url_for('home'))

# Route to display detailed recipe information
@app.route('/recipe/<int:recipe_id>')
def recipe_info(recipe_id):
    recipe_details = get_recipe_information(recipe_id)
    return render_template('recipe_info.html', recipe=recipe_details)

# Route to display liked recipes
@app.route('/liked')
def liked_recipes():
    liked_ids = session.get('liked_recipes', [])
    recipes = [get_recipe_information(recipe_id) for recipe_id in liked_ids]
    return render_template('liked.html', recipes=recipes)

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
        'diet': ','.join(preferences),  # Join preferences into a comma-separated string
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
