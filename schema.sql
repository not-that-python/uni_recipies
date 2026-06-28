-- tables.sql

-- 1. The Recipes Table
CREATE TABLE recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    cooking_time INTEGER NOT NULL, -- in minutes
    cost INTEGER NOT NULL, -- 1 = Cheap, 2 = Medium, 3 = Slightly Pricy
    instructions TEXT NOT NULL,
    image_url TEXT
);

-- 2. The Ingredients Table (Master list)
CREATE TABLE ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- 3. The Junction Table (Links recipes to ingredients)
CREATE TABLE recipe_ingredients (
    recipe_id INTEGER,
    ingredient_id INTEGER,
    quantity TEXT, -- e.g., "2 tbsp", "1 cup"
    FOREIGN KEY (recipe_id) REFERENCES recipes (id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
);

-- Let's seed some student-friendly data
INSERT INTO recipes (name, description, cooking_time, cost, instructions, image_url) 
VALUES 
('5-Minute Mug Omelette', 'Fluffy eggs cooked in a mug in the microwave. Zero pans to wash.', 5, 1, 'Crack 2 eggs into a large mug. Add a splash of milk, salt, and pepper. Whisk with a fork. Microwave for 45 seconds, stir, microwave for another 30 seconds. Top with cheese.', 'https://via.placeholder.com/300x200/FFD700/000000?text=Mega+Omelette'),
('Student Stir-fry', 'A forgiving, cheap stir-fry using whatever veg you have left.', 12, 2, 'Cook noodles according to package. In a hot pan, fry garlic and frozen veg for 3 mins. Add soy sauce, honey, and a splash of water. Toss in the cooked noodles and fry for 2 mins.', 'https://via.placeholder.com/300x200/FF4500/FFFFFF?text=Stir+Fry'),
('Tuna Pasta Bake', 'Makes 4 portions. Eat now, save the rest for tomorrow.', 25, 2, 'Cook pasta. Mix with canned tuna, canned tomatoes, and sweetcorn. Pour into an oven dish, top with cheese, bake at 200C for 15 mins.', 'https://via.placeholder.com/300x200/2E8B57/FFFFFF?text=Pasta+Bake'),
('Beans on Toast (Deluxe)', 'Elevate the classic student staple with spices.', 5, 1, 'Heat baked beans in a pot with a dash of chili flakes and Worcestershire sauce. Toast the bread. Butter the toast, pile on the beans, top with a fried egg (if feeling rich).', 'https://via.placeholder.com/300x200/8B4513/FFFFFF?text=Beans+on+Toast');

-- Ingredients
INSERT INTO ingredients (name) VALUES ('Egg'), ('Milk'), ('Cheese'), ('Garlic'), ('Frozen Vegetables'), ('Soy Sauce'), ('Honey'), ('Noodles'), ('Pasta'), ('Canned Tuna'), ('Canned Tomatoes'), ('Sweetcorn'), ('Bread'), ('Baked Beans'), ('Chili Flakes'), ('Butter');

-- Linking (Recipe 1: Mug Omelette)
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (1, 1, '2 large');
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (1, 2, '1 tbsp');
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (1, 3, 'A handful');

-- Recipe 2: Stir-fry
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (2, 4, '1 clove');
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (2, 5, '2 cups');
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (2, 6, '3 tbsp');
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (2, 7, '1 tbsp');
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (2, 8, '1 pack');

-- Recipe 3: Pasta Bake
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (3, 9, '300g');
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (3, 10, '1 can');
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (3, 11, '1 can');
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (3, 12, '1/2 can');

-- Recipe 4: Beans on Toast
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (4, 13, '2 slices');
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (4, 14, '1 can');
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (4, 15, '1 pinch');
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity) VALUES (4, 16, '1 knob');