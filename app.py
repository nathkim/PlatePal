from flask import Flask, render_template, request, url_for, redirect, session
import requests, os, openai, uuid
from pymongo import MongoClient
from config import SPOONACULAR_API_KEY

openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)

app.secret_key = os.getenv('SESSION_KEY')

MONGO_URI = os.getenv('MONGO_URI')

# MongoDB setup
client = MongoClient(MONGO_URI)  # Connect to MongoDB
db = client['platepal_db']  # Database for storing liked recipes
liked_recipes_collection = db['liked_recipes']  # Collection for liked recipes

@app.before_request
def init_session():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())  # Create a unique session ID

        # Clear all liked recipes associated with this session ID in MongoDB
        liked_recipes_collection.delete_many({'session_id': session['session_id']})

        # Initialize the liked_recipes list in the session
        session['liked_recipes'] = []

# @app.before_request
# def force_new_session():
#     session.clear()

# Home route to display input form
@app.route('/')
def home():
    return render_template('index.html')

# Function to ask ChatGPT to categorize each recipe
def categorize_recipe(recipe):
    prompt = f"Is '{recipe}' considered breakfast, lunch, or dinner one word answer"
    
    # Send the prompt to OpenAI GPT-3.5
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a culinary expert."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10
    )
    
    # Extract the response content (e.g., "breakfast", "lunch", or "dinner")
    answer = response.choices[0].message.content
    
    return answer

# Route to process user input and return recipe search results
@app.route('/recommend', methods=['POST'])
def recommend():
    calorie_intake = int(request.form['calories'])
    dietary_restrictions = request.form.getlist('restrictions')
    dietary_preferences = request.form.getlist('preferences')
    ingredients = request.form.get('ingredients')
    meals_per_day = int(request.form['meals'])

    other_restriction = request.form.get('other-restriction', '').strip()
    if 'Other' in dietary_restrictions and other_restriction:
        dietary_restrictions.append(other_restriction)

    # Calculate calories per meal
    calories_per_meal = calorie_intake // meals_per_day

    # Fetch recipe recommendations
    recipes = get_recipe_recommendations(calories_per_meal, dietary_restrictions, dietary_preferences, ingredients)

    breakfast_list = []
    lunch_list = []
    dinner_list = []

    # Loop through each recipe and categorize it
    for r in recipes:
        category = categorize_recipe(r)
    
        # Sort the recipe into the appropriate list based on the OpenAI response
        if "breakfast" in category.lower():
            breakfast_list.append(r)
        elif "lunch" in category.lower():
            lunch_list.append(r)
        elif "dinner" in category.lower():
            dinner_list.append(r)

    # Pass the categorized lists to the HTML template
    return render_template('results.html', 
                           breakfast_list=breakfast_list, 
                           lunch_list=lunch_list, 
                           dinner_list=dinner_list)

# Route to display detailed recipe information
@app.route('/recipe/<int:recipe_id>')
def recipe_info(recipe_id):
    recipe_details = get_recipe_information(recipe_id)
    return render_template('recipe_info.html', recipe=recipe_details)

# Route to save or remove liked recipes to/from MongoDB Atlas
@app.route('/update_liked_recipes', methods=['POST'])
def update_liked_recipes():
    liked_recipes = request.form.getlist('liked_recipes')  # Get the list of checked recipes

    # Remove all existing liked recipes for the session first
    liked_recipes_collection.delete_many({'session_id': session['session_id']})

    # Re-add the ones that are still liked (i.e., checked in the form)
    for recipe_id in liked_recipes:
        liked_recipes_collection.insert_one({'recipe_id': recipe_id, 'session_id': session['session_id']})

    return redirect(url_for('liked_recipes'))

# Route to display liked recipes (liked.html)
@app.route('/liked')
def liked_recipes():
    # Get all liked recipe IDs from MongoDB
    liked_recipe_ids = [recipe['recipe_id'] for recipe in liked_recipes_collection.find({'session_id': session['session_id']})]    
    # Fetch additional details about liked recipes if needed
    liked_recipes_data = []
    for recipe_id in liked_recipe_ids:
        recipe_details = get_recipe_information(recipe_id)
        if recipe_details:
            liked_recipes_data.append(recipe_details)
    
    return render_template('liked.html', liked_recipes=liked_recipes_data)

@app.route('/schedule')
def schedule():
    return render_template('schedule.html')

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
def get_recipe_recommendations(calories_per_meal, restrictions, preferences, ingredients, number_of_recipes=25):
    url = f"https://api.spoonacular.com/recipes/complexSearch"
    all_results = []
    ingredient_list = []
    if ingredients:
        ingredient_list = [ingredient.strip() for ingredient in ingredients.split(',')]

        for i in ingredient_list:
            params = {
                'apiKey': SPOONACULAR_API_KEY,
                'maxCalories': calories_per_meal,
                'diet': ','.join(preferences),
                'intolerances': ','.join(restrictions),
                'includeIngredients': i,
                'number': 5
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                all_results.extend(response.json().get('results', []))  # Combine results
            else:
                print(f"Error: {response.status_code}")

    # Calculate the remaining number of recipes to fetch, ensuring it's non-negative
    remaining_recipes = number_of_recipes - len(ingredient_list) * 5
    if remaining_recipes > 0:
        params = {
            'apiKey': SPOONACULAR_API_KEY,
            'maxCalories': calories_per_meal,
            'diet': ','.join(preferences),
            'intolerances': ','.join(restrictions),
            'number': remaining_recipes
        }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        all_results.extend(response.json().get('results', []))  # Combine results
    else:
        print(f"Error: {response.status_code}")
    
    return all_results

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