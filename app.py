from flask import Flask, render_template, request, url_for
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

def clean_price(price_str):
    """Convert price string to float, removing currency symbols and commas."""
    if not price_str or price_str == "Price not found":
        return float('inf')
    return float(price_str.replace('$', '').replace(',', '').replace(' USD', ''))

def load_ski_data():
    """Load and return ski data from JSON file."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, 'ski_prices.json')
        with open(json_path, 'r') as f:
            data = json.load(f)
            return data['skis']
    except FileNotFoundError:
        print("Warning: ski_prices.json not found")
        return []
    except json.JSONDecodeError:
        print("Warning: Invalid JSON in ski_prices.json")
        return []

def get_image_path(ski_name):
    """Convert ski name to a valid filename and check if image exists."""
    # Remove year and 'Skis' from the name, and clean up special characters
    cleaned_name = ski_name.lower()
    cleaned_name = cleaned_name.replace('skis', '').replace('2024', '').replace('2025', '').replace('2026', '')
    cleaned_name = cleaned_name.replace('|', '').replace('  ', ' ').strip()
    
    # Handle special cases for our specific skis
    if "black crow mirus cor" in cleaned_name or "black crows mirus cor" in cleaned_name:
        filename = "black_crows_mirus_cor"
    elif "stockli montero ar" in cleaned_name:
        filename = "stockli_montero_ar"
    elif "volkl my mantra" in cleaned_name or "völkl my mantra" in cleaned_name:
        filename = "völkl_m7_mantra"
    else:
        # Default case: Replace spaces and special chars with underscores
        filename = cleaned_name.replace(' ', '_').replace('-', '_')
    
    print(f"Original ski name: {ski_name}")
    print(f"Cleaned filename: {filename}")
    
    # Check for different possible extensions
    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
        image_path = f'images/skis/{filename}{ext}'
        full_path = os.path.join('static', image_path)
        print(f"Checking path: {full_path}")
        if os.path.exists(full_path):
            print(f"Found image at: {image_path}")
            return image_path
    
    print(f"No image found for {ski_name}, using default")
    return 'images/skis/default_ski.jpg'

def find_best_deals(search_query=None):
    """Find best deals for skis, optionally filtered by search query."""
    ski_data = load_ski_data()
    
    if search_query:
        # Filter skis based on search query
        matching_skis = []
        search_query = search_query.lower()
        for ski in ski_data:
            if search_query in ski['ski_name'].lower():
                matching_skis.append(ski)
        ski_data = matching_skis
    else:
        # For the landing page, show our three specific skis
        mirus_cor_options = []
        montero_options = []
        mantra_options = []
        
        for ski in ski_data:
            if "Black Crows Mirus Cor" in ski['ski_name']:
                ski['ski_name'] = "2025 Black Crow Mirus Cor"  # Update name
                mirus_cor_options.append(ski)
            elif "Stockli Montero AR" in ski['ski_name']:
                ski['ski_name'] = "2025 Stockli Montero AR"  # Update name
                montero_options.append(ski)
            elif "M7 Mantra" in ski['ski_name'] or "Völkl M7 Mantra" in ski['ski_name']:
                ski['ski_name'] = "2025 Volkl MY Mantra"  # Update name
                mantra_options.append(ski)
        
        # Sort each list by price and get the cheapest option
        ski_data = []
        if mirus_cor_options:
            mirus_cor_options.sort(key=lambda x: clean_price(x['current_price']))
            ski_data.append(mirus_cor_options[0])
        if montero_options:
            montero_options.sort(key=lambda x: clean_price(x['current_price']))
            ski_data.append(montero_options[0])
        if mantra_options:
            mantra_options.sort(key=lambda x: clean_price(x['current_price']))
            ski_data.append(mantra_options[0])
    
    # Format the results
    formatted_results = []
    for ski in ski_data:
        # Get the local image path for this ski
        image_path = get_image_path(ski['ski_name'])
        
        formatted_results.append({
            'name': ski['ski_name'],
            'deals': [{
                'price': ski['current_price'],
                'store': ski['site_name'],
                'url': ski['site_url'],
                'image_url': url_for('static', filename=image_path)
            }]
        })
    
    return formatted_results

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        # Always load default skis first
        default_skis = find_best_deals()
        search_results = None

        if request.method == 'POST':
            search_query = request.form.get('ski_name', '').strip()
            if search_query:
                search_results = find_best_deals(search_query)
                print(f"Found {len(search_results)} results for '{search_query}'")
        
        return render_template('index.html', 
                             default_skis=default_skis if default_skis else None,
                             search_results=search_results if search_results else None)
    
    except Exception as e:
        print(f"Error in index route: {str(e)}")
        return render_template('index.html', default_skis=[], search_results=None)

@app.route('/update-prices')
def update_prices():
    update_ski_prices()
    return "Prices updated successfully!"

if __name__ == '__main__':
    # Development server configuration
    app.run(
        host='127.0.0.1',  # Only allow local connections
        port=5000,
        debug=True
    ) 