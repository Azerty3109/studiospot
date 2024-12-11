from flask import Flask, render_template, request, redirect, url_for, flash, session
from supabase import create_client, Client
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Supabase Configuration
SUPABASE_URL = "https://pfdxdcimgfqynwsjealj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBmZHhkY2ltZ2ZxeW53c2plYWxqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzMyMTIxMjAsImV4cCI6MjA0ODc4ODEyMH0.fRQKYovmlnZPh8GvnRjZytLf9x0Cd-D0CYadvpDc0GA"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        confirm_password = request.form.get('confirm_password').strip()

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        try:
            # Check if username exists
            existing_user = supabase.table('users').select('*').eq('username', username).execute()
            if existing_user.data:
                flash('Username already exists.', 'error')
                return redirect(url_for('register'))

            # Insert new user
            supabase.table('users').insert({
                'username': username,
                'password': password  # In production, use password hashing
            }).execute()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()

        try:
            # Admin login
            if username == "admin" and password == "admin123":
                session['username'] = username
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_manage_recipe'))

            # Regular user login
            user = supabase.table('users').select('*')\
                .eq('username', username)\
                .eq('password', password)\
                .execute()

            if user.data:
                session['username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('main_dashboard'))
            else:
                flash('Invalid username or password.', 'error')

        except Exception as e:
            flash(f"Error: {str(e)}", 'error')

    return render_template('login.html')

@app.route('/main_dashboard')
def main_dashboard():
    if 'username' not in session:
        flash('You must log in to access the dashboard.', 'error')
        return redirect(url_for('login'))

    try:
        recipes = supabase.table('recipes').select('*').execute()
        return render_template('main_dashboard.html', 
                             username=session['username'], 
                             recipes=recipes.data)
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('login'))

@app.route('/recipes')
def recipe():
    try:
        recipes = supabase.table('recipes').select('*').execute()
        
        # Group recipes by category
        categorized_recipes = {}
        for recipe in recipes.data:
            category = recipe['category']
            if category not in categorized_recipes:
                categorized_recipes[category] = []
            categorized_recipes[category].append(recipe)

        return render_template('recipe.html', categorized_recipes=categorized_recipes)
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('main_dashboard'))

@app.route('/favorite_list')
def favorite_list():
    if 'username' not in session:
        flash('You must log in to view favorites.', 'error')
        return redirect(url_for('login'))

    try:
        # Get user ID
        user = supabase.table('users').select('id')\
            .eq('username', session['username'])\
            .execute()
        
        if not user.data:
            flash('User not found.', 'error')
            return redirect(url_for('login'))

        user_id = user.data[0]['id']

        # Get favorite recipes
        favorites = supabase.table('favorites')\
            .select('recipes(*)')\
            .eq('user_id', user_id)\
            .execute()

        return render_template('favorite_list.html', favorites=favorites.data)
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('main_dashboard'))

@app.route('/add_to_favorites/<recipe_id>', methods=['POST'])
def add_to_favorites(recipe_id):
    if 'username' not in session:
        flash('You must log in to add favorites.', 'error')
        return redirect(url_for('login'))

    try:
        # Get user ID
        user = supabase.table('users').select('id')\
            .eq('username', session['username'])\
            .execute()
        
        if not user.data:
            flash('User not found.', 'error')
            return redirect(url_for('login'))

        user_id = user.data[0]['id']

        # Add to favorites
        supabase.table('favorites').insert({
            'user_id': user_id,
            'recipe_id': recipe_id
        }).execute()

        flash('Recipe added to favorites!', 'success')
        return redirect(url_for('favorite_list'))
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('main_dashboard'))

@app.route('/admin_manage_recipe', methods=['GET', 'POST'])
def admin_manage_recipe():
    if request.method == 'POST':
        if 'action' in request.form:
            recipe_id = request.form.get('recipe_id')
            action = request.form.get('action')

            try:
                if action == 'delete':
                    # Delete recipe
                    supabase.table('recipes')\
                        .delete()\
                        .eq('id', recipe_id)\
                        .execute()
                    flash('Recipe deleted successfully!', 'success')
                elif action == 'edit':
                    return redirect(url_for('update_recipe', recipe_id=recipe_id))
            except Exception as e:
                flash(f"Error: {str(e)}", 'error')
        else:
            # Add new recipe
            try:
                name = request.form.get('name')
                category = request.form.get('category')
                ingredient = request.form.get('ingredient')
                instructions = request.form.get('instructions')
                time = request.form.get('time')
                image = request.files.get('image')

                if image:
                    filename = secure_filename(image.filename)
                    image_path = os.path.join('static', 'images', filename)
                    image.save(image_path)
                else:
                    image_path = None

                supabase.table('recipes').insert({
                    'name': name,
                    'category': category,
                    'ingredient': ingredient,
                    'instructions': instructions,
                    'time': time,
                    'image_url': image_path
                }).execute()

                flash('Recipe added successfully!', 'success')
            except Exception as e:
                flash(f"Error: {str(e)}", 'error')

    try:
        recipes = supabase.table('recipes').select('*').execute()
        return render_template('admin_manage_recipe.html', recipes=recipes.data)
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('login'))

@app.route('/chicken')
def chicken():
    if 'username' not in session:
        flash('You must log in to view recipes.', 'error')
        return redirect(url_for('login'))

    try:
        response = supabase.table('recipe')\
            .select('name, image_url, time')\
            .eq('category', 'Chicken')\
            .execute()
            
        if not response.data:
            flash('No chicken recipes found.', 'info')
            return redirect(url_for('chicken'))
            
        return render_template('chicken.html', 
                             chicken_recipes=response.data, 
                             category='Chicken')
                             
    except Exception as e:
        flash(f"Error fetching chicken recipes: {str(e)}", 'error')
        return redirect(url_for('main_dashboard'))

@app.route('/beef')
def beef():
    if 'username' not in session:
        flash('You must log in to view recipes.', 'error')
        return redirect(url_for('login'))

    try:
        response = supabase.table('recipe')\
            .select('name, image_url, time')\
            .eq('category', 'Beef')\
            .execute()
            
        if not response.data:
            flash('No beef recipes found.', 'info')
            return redirect(url_for('main_dashboard'))
            
        return render_template('beef.html', 
                             beef_recipes=response.data,
                             category='Beef')
                             
    except Exception as e:
        flash(f"Error fetching beef recipes: {str(e)}", 'error')
        return redirect(url_for('main_dashboard'))

@app.route('/pork')
def pork():
    if 'username' not in session:
        flash('You must log in to view recipes.', 'error')
        return redirect(url_for('login'))

    try:
        response = supabase.table('recipe')\
            .select('name, image_url, time')\
            .eq('category', 'Pork')\
            .execute()
            
        if not response.data:
            flash('No pork recipes found.', 'info')
            return redirect(url_for('main_dashboard'))
            
        return render_template('pork.html', 
                             pork_recipes=response.data,
                             category='Pork')
                             
    except Exception as e:
        flash(f"Error fetching pork recipes: {str(e)}", 'error')
        return redirect(url_for('main_dashboard'))

@app.route('/egg')
def egg():
    if 'username' not in session:
        flash('You must log in to view recipes.', 'error')
        return redirect(url_for('login'))

    try:
        response = supabase.table('recipe')\
            .select('name, image_url, time')\
            .eq('category', 'Egg')\
            .execute()
            
        if not response.data:
            flash('No egg recipes found.', 'info')
            return redirect(url_for('main_dashboard'))
            
        return render_template('egg.html', 
                             egg_recipes=response.data,
                             category='Egg')
                             
    except Exception as e:
        flash(f"Error fetching egg recipes: {str(e)}", 'error')
        return redirect(url_for('main_dashboard'))

@app.route('/soup')
def soup():
    if 'username' not in session:
        flash('You must log in to view recipes.', 'error')
        return redirect(url_for('login'))

    try:
        response = supabase.table('recipe')\
            .select('name, image_url, time')\
            .eq('category', 'Soup')\
            .execute()
            
        if not response.data:
            flash('No soup recipes found.', 'info')
            return redirect(url_for('main_dashboard'))
            
        return render_template('soup.html', 
                             soup_recipes=response.data,
                             category='Soup')
                             
    except Exception as e:
        flash(f"Error fetching soup recipes: {str(e)}", 'error')
        return redirect(url_for('main_dashboard'))

@app.route('/bread')
def bread():
    if 'username' not in session:
        flash('You must log in to view recipes.', 'error')
        return redirect(url_for('login'))

    try:
        response = supabase.table('recipe')\
            .select('name, image_url, time')\
            .eq('category', 'Bread')\
            .execute()
            
        if not response.data:
            flash('No bread recipes found.', 'info')
            return redirect(url_for('main_dashboard'))
            
        return render_template('bread.html', 
                             bread_recipes=response.data,
                             category='Bread')
                             
    except Exception as e:
        flash(f"Error fetching bread recipes: {str(e)}", 'error')
        return redirect(url_for('main_dashboard'))

@app.route('/ingredient/<category>/<name>')
def ingredient(category, name):
    if 'username' not in session:
        flash('You must log in to view recipes.', 'error')
        return redirect(url_for('login'))

    try:
        response = supabase.table('recipe')\
            .select('*')\
            .eq('category', category)\
            .eq('name', name)\
            .execute()

        if not response.data:
            flash('Recipe not found.', 'error')
            return redirect(url_for(category.lower()))  # Redirect to category page

        recipe = response.data[0]
        recipe['ingredient'] = recipe['ingredient'].split(',') if recipe['ingredient'] else []
        recipe['instructions'] = recipe['instructions'].split('\n') if recipe['instructions'] else []

        return render_template('ingredient.html', 
                             recipe=recipe, 
                             category=category)
                             
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for(category.lower()))  # Redirect to category page

if __name__ == '__main__':
    app.run(debug=True)

