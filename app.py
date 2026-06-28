# app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import json

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('recipes.db')
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add')
def add_recipe_page():
    return render_template('add.html')

# API 1: Get ALL recipes (for the main feed)
@app.route('/api/recipes')
def get_recipes():
    conn = get_db_connection()
    recipes = conn.execute('SELECT * FROM recipes').fetchall()
    conn.close()
    return jsonify([dict(row) for row in recipes])

# API 2: The "Pantry Search" - finds recipes based on ingredients you have
@app.route('/api/search', methods=['POST'])
def search_by_ingredients():
    data = request.get_json()
    user_ingredients = data.get('ingredients', []) # e.g., ["Egg", "Milk", "Cheese"]
    
    if not user_ingredients:
        return jsonify([])

    # Build a dynamic SQL query to find recipes that contain ALL listed ingredients
    placeholders = ','.join(['?'] * len(user_ingredients))
    
    query = f"""
        SELECT r.*, COUNT(ri.ingredient_id) as match_count
        FROM recipes r
        JOIN recipe_ingredients ri ON r.id = ri.recipe_id
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE i.name IN ({placeholders})
        GROUP BY r.id
        HAVING match_count = ?
        ORDER BY r.cost ASC, r.cooking_time ASC
    """
    
    # The '?' parameters: the list of ingredients, and the length of that list (to ensure ALL are matched)
    params = user_ingredients + [len(user_ingredients)]
    
    conn = get_db_connection()
    results = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in results])

# API 3: Get details of a single recipe (for the modal/popup)
@app.route('/api/recipe/<int:recipe_id>')
def get_recipe_detail(recipe_id):
    conn = get_db_connection()
    recipe = conn.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,)).fetchone()
    
    # Get the full ingredient list with quantities for this specific recipe
    ingredients = conn.execute('''
        SELECT i.name, ri.quantity 
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id = ?
    ''', (recipe_id,)).fetchall()
    
    conn.close()
    
    return jsonify({
        'recipe': dict(recipe),
        'ingredients': [dict(row) for row in ingredients]
    })

# API 4: Add a new recipe
@app.route('/api/recipes', methods=['POST'])
def add_recipe():
    data = request.get_json()
    
    # Validate required fields
    required = ['name', 'description', 'cooking_time', 'cost', 'instructions', 'ingredients']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Insert the recipe
        cursor.execute('''
            INSERT INTO recipes (name, description, cooking_time, cost, instructions, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data['description'],
            data['cooking_time'],
            data['cost'],
            data['instructions'],
            data.get('image_url', 'https://via.placeholder.com/300x200/F0F0F0/555555?text=New+Recipe')
        ))
        
        recipe_id = cursor.lastrowid
        
        # 2. Process each ingredient
        for ingredient_data in data['ingredients']:
            ingredient_name = ingredient_data['name'].strip().capitalize()
            quantity = ingredient_data.get('quantity', '')
            
            # Check if ingredient exists, if not create it
            cursor.execute('SELECT id FROM ingredients WHERE name = ?', (ingredient_name,))
            result = cursor.fetchone()
            
            if result:
                ingredient_id = result[0]
            else:
                cursor.execute('INSERT INTO ingredients (name) VALUES (?)', (ingredient_name,))
                ingredient_id = cursor.lastrowid
            
            # Link ingredient to recipe
            cursor.execute('''
                INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity)
                VALUES (?, ?, ?)
            ''', (recipe_id, ingredient_id, quantity))
        
        conn.commit()
        return jsonify({
            'message': 'Recipe added successfully!',
            'recipe_id': recipe_id
        }), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# API 5: Get all ingredients (for autocomplete)
@app.route('/api/ingredients')
def get_ingredients():
    conn = get_db_connection()
    ingredients = conn.execute('SELECT name FROM ingredients ORDER BY name').fetchall()
    conn.close()
    return jsonify([row[0] for row in ingredients])

if __name__ == '__main__':
    app.run(debug=True)