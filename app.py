# app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import os

app = Flask(__name__)
CORS(app)

# Load environment variables from .env file
load_dotenv()

# Get the secret key
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key-for-testing')

# Use it in your app
app.secret_key = SECRET_KEY

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def parse_category_ids(raw_ids):
    """Coerces a list of category ids (from query string or JSON body) to ints, dropping anything invalid."""
    ids = []
    for raw_id in raw_ids:
        try:
            ids.append(int(raw_id))
        except (TypeError, ValueError):
            continue
    return ids

def get_category_matching_recipe_ids(conn, category_ids):
    """Recipe ids that have at least one of the selected categories per type (AND across types, OR within a type)."""
    if not category_ids:
        return None
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    placeholders = ','.join(['%s'] * len(category_ids))
    cur.execute(
        f'SELECT COUNT(DISTINCT type) as type_count FROM categories WHERE id IN ({placeholders})', category_ids
    )
    type_count = cur.fetchone()['type_count']
    cur.execute(f'''
        SELECT rc.recipe_id
        FROM recipe_categories rc
        JOIN categories c ON c.id = rc.category_id
        WHERE rc.category_id IN ({placeholders})
        GROUP BY rc.recipe_id
        HAVING COUNT(DISTINCT c.type) = %s
    ''', category_ids + [type_count])
    rows = cur.fetchall()
    cur.close()
    return {row['recipe_id'] for row in rows}

def attach_categories(conn, recipes):
    """Attaches a 'categories' list (each {id, name, type}) to every recipe row."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    result = []
    for r in recipes:
        cur.execute('''
            SELECT c.id, c.name, c.type
            FROM recipe_categories rc
            JOIN categories c ON c.id = rc.category_id
            WHERE rc.recipe_id = %s
            ORDER BY c.type, c.name
        ''', (r['id'],))
        cats = cur.fetchall()
        recipe_dict = dict(r)
        recipe_dict['categories'] = [dict(c) for c in cats]
        result.append(recipe_dict)
    cur.close()
    return result

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add')
def add_recipe_page():
    return render_template('add.html')

# API 1: Get ALL recipes (for the main feed), optionally filtered by ?category_ids=1,2,3
@app.route('/api/recipes')
def get_recipes():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    category_ids = parse_category_ids(request.args.get('category_ids', '').split(','))

    matching_ids = get_category_matching_recipe_ids(conn, category_ids)
    if matching_ids is not None:
        if not matching_ids:
            cur.close()
            conn.close()
            return jsonify([])
        placeholders = ','.join(['%s'] * len(matching_ids))
        cur.execute(f'SELECT * FROM recipes WHERE id IN ({placeholders})', list(matching_ids))
    else:
        cur.execute('SELECT * FROM recipes')
    recipes = cur.fetchall()

    result = attach_categories(conn, recipes)
    cur.close()
    conn.close()
    return jsonify(result)

# API 2: The "Pantry Search" - finds recipes based on ingredients you have, optionally also filtered by category_ids
@app.route('/api/search', methods=['POST'])
def search_by_ingredients():
    data = request.get_json()
    user_ingredients = data.get('ingredients', []) # e.g., ["Egg", "Milk", "Cheese"]
    category_ids = parse_category_ids(data.get('category_ids', []))

    if not user_ingredients:
        return jsonify([])

    # Build a dynamic SQL query to find recipes that contain ALL listed ingredients
    placeholders = ','.join(['%s'] * len(user_ingredients))

    query = f"""
        SELECT r.*, COUNT(ri.ingredient_id) as match_count
        FROM recipes r
        JOIN recipe_ingredients ri ON r.id = ri.recipe_id
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE i.name IN ({placeholders})
        GROUP BY r.id
        HAVING COUNT(ri.ingredient_id) = %s
        ORDER BY r.cost ASC, r.cooking_time ASC
    """

    # The '%s' parameters: the list of ingredients, and the length of that list (to ensure ALL are matched)
    params = user_ingredients + [len(user_ingredients)]

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query, params)
    results = cur.fetchall()

    matching_ids = get_category_matching_recipe_ids(conn, category_ids)
    if matching_ids is not None:
        results = [r for r in results if r['id'] in matching_ids]

    response = attach_categories(conn, results)
    cur.close()
    conn.close()

    return jsonify(response)

# API 3: Get details of a single recipe (for the modal/popup)
@app.route('/api/recipe/<int:recipe_id>')
def get_recipe_detail(recipe_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT * FROM recipes WHERE id = %s', (recipe_id,))
    recipe = cur.fetchone()

    # Get the full ingredient list with quantities for this specific recipe
    cur.execute('''
        SELECT i.name, ri.quantity
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id = %s
    ''', (recipe_id,))
    ingredients = cur.fetchall()

    cur.execute('''
        SELECT c.id, c.name, c.type
        FROM recipe_categories rc
        JOIN categories c ON c.id = rc.category_id
        WHERE rc.recipe_id = %s
        ORDER BY c.type, c.name
    ''', (recipe_id,))
    categories = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        'recipe': dict(recipe),
        'ingredients': [dict(row) for row in ingredients],
        'categories': [dict(row) for row in categories]
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
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # 1. Insert the recipe
        cursor.execute('''
            INSERT INTO recipes (name, description, cooking_time, cost, instructions, image_url)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        ''', (
            data['name'],
            data['description'],
            data['cooking_time'],
            data['cost'],
            data['instructions'],
            data.get('image_url', 'https://via.placeholder.com/300x200/F0F0F0/555555?text=New+Recipe')
        ))

        recipe_id = cursor.fetchone()['id']

        # 2. Process each ingredient
        for ingredient_data in data['ingredients']:
            ingredient_name = ingredient_data['name'].strip().capitalize()
            quantity = ingredient_data.get('quantity', '')

            # Check if ingredient exists, if not create it
            cursor.execute('SELECT id FROM ingredients WHERE name = %s', (ingredient_name,))
            result = cursor.fetchone()

            if result:
                ingredient_id = result['id']
            else:
                cursor.execute('INSERT INTO ingredients (name) VALUES (%s) RETURNING id', (ingredient_name,))
                ingredient_id = cursor.fetchone()['id']

            # Link ingredient to recipe
            cursor.execute('''
                INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity)
                VALUES (%s, %s, %s)
            ''', (recipe_id, ingredient_id, quantity))

        # 3. Process each category (freeform, e.g. {"name": "Indian", "type": "Cuisine"})
        for category_data in data.get('categories', []):
            category_name = category_data['name'].strip().title()
            category_type = category_data['type'].strip().title()
            if not category_name or not category_type:
                continue

            # Check if category exists, if not create it
            cursor.execute('SELECT id FROM categories WHERE name = %s AND type = %s', (category_name, category_type))
            result = cursor.fetchone()

            if result:
                category_id = result['id']
            else:
                cursor.execute('INSERT INTO categories (name, type) VALUES (%s, %s) RETURNING id', (category_name, category_type))
                category_id = cursor.fetchone()['id']

            # Link category to recipe
            cursor.execute('''
                INSERT INTO recipe_categories (recipe_id, category_id)
                VALUES (%s, %s)
            ''', (recipe_id, category_id))

        conn.commit()
        return jsonify({
            'message': 'Recipe added successfully!',
            'recipe_id': recipe_id
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# API 5: Get all ingredients (for autocomplete)
@app.route('/api/ingredients')
def get_ingredients():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT name FROM ingredients ORDER BY name')
    ingredients = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([row[0] for row in ingredients])

# API 6: Get all categories, grouped by type (for the filter UI and add-recipe autocomplete)
@app.route('/api/categories')
def get_categories():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('SELECT id, name, type FROM categories ORDER BY type, name')
    categories = cur.fetchall()
    cur.close()
    conn.close()

    grouped = {}
    for c in categories:
        grouped.setdefault(c['type'], []).append({'id': c['id'], 'name': c['name']})

    return jsonify(grouped)

@app.route('/help')
def help_page():
    return render_template('help.html')

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
