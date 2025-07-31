from flask import Flask, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
import bcrypt
from flask_cors import CORS
from datetime import datetime
import json

# Import recommendation functions
from recommendation_model import (
    get_recommendations, 
    get_popular_recommendations,
    get_recommendations_by_state,
    get_recommendations_by_type,
    analyze_wishlist_preferences,
    get_trending_recommendations,
    get_seasonal_recommendations,
    get_similar_to_destination,
    get_destination_details
)
from places_data import places
import openai

# Flask setup — serves everything from the 'public' folder
app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)  # Allow all origins
app.secret_key = 'your_secret_key'
openai.api_key = 'your_openai_api_key'  # Replace with your real OpenAI key

def get_user_email():
    return session.get("email")

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["voyagevista"]
users_collection = db["users"]
wishlists = db["wishlists"]
reviews = db["reviews"]
user_activity = db["user_activity"]  # Define user_activity collection

# Helper function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Helper to verify passwords
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Routes

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')  # This serves public/index.html

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:
            return jsonify({"error": "Missing fields"}), 400

        if users_collection.find_one({"email": email}):
            return jsonify({"error": "Email already registered"}), 400

        hashed_pw = hash_password(password).decode('utf-8')
        users_collection.insert_one({
            "username": username,
            "email": email,
            "password": hashed_pw
        })

        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        print("Registration error:", e)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if check_password(password, user["password"]):
        session['email'] = user['email']
        session['username'] = user.get('username', '')  # Add username to session
        return jsonify({"message": f"Welcome {user['username']}!"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401
    
# Add a new review
@app.route('/api/reviews', methods=['POST'])
def add_review():
    data = request.get_json()
    review = {
        "username": data.get("username"),
        "location": data.get("location"),
        "experience": data.get("experience"),
        "date_posted": datetime.utcnow()
    }
    reviews.insert_one(review)
    return jsonify({"message": "Review added successfully"}), 201

# Get all reviews
@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    all_reviews = reviews.find().sort("date_posted", -1)
    result = []
    for r in all_reviews:
        result.append({
            "username": r["username"],
            "location": r["location"],
            "experience": r["experience"],
            "date_posted": r["date_posted"].strftime("%Y-%m-%d %H:%M")
        })
    return jsonify(result)

@app.route('/api/search_suggestions')
def search_suggestions():
    query = request.args.get('q', '').lower()
    # print("Received query:", query)

    matched_places = []
    for place_name in places:
        if query in place_name.lower():
            matched_places.append(place_name)
            matched_places.append(places[place_name])

    return jsonify({"suggestions": matched_places})

@app.route('/api/wishlist/add', methods=['POST'])
def add_to_wishlist():
    """Add an item to user's wishlist"""
    try:
        user_email = session.get('email')
        if not user_email:
            return jsonify({"error": "User not logged in"}), 401
            
        data = request.json
        item = data.get('item')
        if not item:
            return jsonify({"error": "No item provided"}), 400
            
        # Check if user already has a wishlist
        user_wishlist = wishlists.find_one({"user_email": user_email})
        
        if user_wishlist:
            # Check if item already exists in wishlist
            existing_items = user_wishlist.get('items', [])
            if any(existing['spot_id'] == item['spot_id'] for existing in existing_items):
                return jsonify({"message": "Item already in wishlist"}), 200
                
            # Add item to existing wishlist
            wishlists.update_one(
                {"user_email": user_email},
                {"$push": {"items": item}}
            )
        else:
            # Create new wishlist for user
            wishlists.insert_one({
                "user_email": user_email,
                "items": [item],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
        
        return jsonify({"message": "Added to wishlist"}), 201
        
    except Exception as e:
        print("Wishlist add error:", str(e))
        return jsonify({"error": "Failed to add to wishlist", "details": str(e)}), 500

@app.route('/api/wishlist', methods=['GET'])
def get_wishlist():
    """Get user's wishlist"""
    try:
        user_email = session.get('email')
        if not user_email:
            return jsonify({"error": "User not logged in"}), 401
            
        # Get user's wishlist from database
        user_wishlist = wishlists.find_one({"user_email": user_email})
        
        if not user_wishlist or 'items' not in user_wishlist:
            return jsonify({"items": []})
            
        return jsonify({"items": user_wishlist['items']})
        
    except Exception as e:
        print("Wishlist get error:", str(e))
        return jsonify({"error": "Failed to get wishlist", "details": str(e)}), 500

@app.route('/api/wishlist/remove', methods=['POST'])
def remove_from_wishlist():
    """Remove an item from user's wishlist"""
    try:
        user_email = session.get('email')
        if not user_email:
            return jsonify({"error": "User not logged in"}), 401
            
        data = request.json
        spot_id = data.get('spot_id')
        if not spot_id:
            return jsonify({"error": "No spot_id provided"}), 400
            
        # Remove item from wishlist
        result = wishlists.update_one(
            {"user_email": user_email},
            {"$pull": {"items": {"spot_id": spot_id}}}
        )
        
        if result.modified_count == 0:
            return jsonify({"message": "Item not found in wishlist"}), 404
            
        return jsonify({"message": "Removed from wishlist"}), 200
        
    except Exception as e:
        print("Wishlist remove error:", str(e))
        return jsonify({"error": "Failed to remove from wishlist", "details": str(e)}), 500

# ----- NEW RECOMMENDATION ROUTES -----

@app.route('/api/recommendations/wishlist', methods=['GET'])
def get_wishlist_recommendations():
    """Get recommendations based on user's wishlist"""
    try:
        # Get user email from session
        user_email = session.get('email')
        if not user_email:
            return jsonify({"error": "User not logged in"}), 401
            
        # Get wishlist from request or localStorage
        wishlist_data = request.args.get('wishlist')
        
        if wishlist_data:
            # If wishlist was sent in request
            wishlist = json.loads(wishlist_data)
            wishlist_titles = [item.get('name') for item in wishlist if item.get('name')]
        else:
            # Try to get from MongoDB
            db_wishlist = wishlists.find_one({"user_email": user_email})
            if db_wishlist and 'items' in db_wishlist:
                wishlist_titles = [item.get('name') for item in db_wishlist['items'] if item.get('name')]
            else:
                wishlist_titles = []
                
        # Get recommendations based on wishlist
        if not wishlist_titles:
            recommended = get_popular_recommendations(5)
            rec_type = "popular"
        else:
            recommended = get_recommendations(wishlist_titles, 5)
            rec_type = "wishlist"
            
        # Track this recommendation request
        user_activity.insert_one({
            "user_email": user_email,
            "activity_type": "recommendation_request",
            "recommendation_type": rec_type,
            "timestamp": datetime.utcnow()
        })
        
        # Return recommendations with detailed information
        recommendations = []
        for title in recommended:
            details = get_destination_details(title)
            if details:
                # Extract state from details to determine link
                state = details.get('state', '').lower()
                link = f"{state}.html" if state in ['kerala', 'karnataka', 'maharashtra'] else "destinations.html"
                
                # Construct image path based on naming patterns in your existing site
                # This is a simplification - in reality you'd need proper image mapping
                recommendations.append({
                    "id": title.lower().replace(' ', '-'),
                    "title": title,
                    "description": f"A beautiful destination in {state.capitalize()}",
                    "image": f"images/{abs(hash(title)) % 90 + 10}.jpg",  # Use abs() for hash value
                    "tags": details.get('tags', '').split()[:4],  # Get first 4 tags
                    "type": details.get('type', 'destination'),
                    "state": state,
                    "link": link
                })
        
        return jsonify({"recommendations": recommendations})
        
    except Exception as e:
        print("Recommendation error:", str(e))
        return jsonify({"error": "Failed to generate recommendations", "details": str(e)}), 500

@app.route('/api/recommendations/popular', methods=['GET'])
def get_popular_recs():
    """Get popular destination recommendations"""
    try:
        # Get popular recommendations
        popular = get_popular_recommendations(6)
        
        # Format recommendations with details
        recommendations = []
        for title in popular:
            details = get_destination_details(title)
            if details:
                state = details.get('state', '').lower()
                link = f"{state}.html" if state in ['kerala', 'karnataka', 'maharashtra'] else "destinations.html"
                
                recommendations.append({
                    "id": title.lower().replace(' ', '-'),
                    "title": title,
                    "description": f"A popular destination in {state.capitalize()}",
                    "image": f"images/{abs(hash(title)) % 90 + 10}.jpg",  # Use abs() for hash value
                    "tags": details.get('tags', '').split()[:4],
                    "type": details.get('type', 'destination'),
                    "state": state,
                    "link": link
                })
        
        return jsonify({"recommendations": recommendations})
        
    except Exception as e:
        print("Popular recommendation error:", str(e))
        return jsonify({"error": "Failed to get popular recommendations", "details": str(e)}), 500

@app.route('/api/recommendations/trending', methods=['GET'])
def get_trending_recs():
    """Get trending destination recommendations"""
    try:
        # Get trending recommendations
        trending = get_trending_recommendations(6)
        
        # Format recommendations with details
        recommendations = []
        for title in trending:
            details = get_destination_details(title)
            if details:
                state = details.get('state', '').lower()
                link = f"{state}.html" if state in ['kerala', 'karnataka', 'maharashtra'] else "destinations.html"
                
                recommendations.append({
                    "id": title.lower().replace(' ', '-'),
                    "title": title,
                    "description": f"A trending destination in {state.capitalize()}",
                    "image": f"images/{abs(hash(title)) % 90 + 10}.jpg",  # Use abs() for hash value
                    "tags": details.get('tags', '').split()[:4],
                    "type": details.get('type', 'destination'),
                    "state": state,
                    "link": link
                })
        
        return jsonify({"recommendations": recommendations})
        
    except Exception as e:
        print("Trending recommendation error:", str(e))
        return jsonify({"error": "Failed to get trending recommendations", "details": str(e)}), 500

@app.route('/api/recommendations/similar', methods=['GET'])
def get_similar_recs():
    """Get recommendations similar to a given destination"""
    try:
        # Get destination from request
        destination = request.args.get('destination')
        if not destination:
            # If no destination provided, try to get last viewed
            user_email = session.get('email')
            if user_email:
                last_activity = user_activity.find_one(
                    {"user_email": user_email, "activity_type": "view_destination"},
                    sort=[("timestamp", -1)]
                )
                if last_activity:
                    destination = last_activity.get('destination')
        
        # If we still don't have a destination, return popular
        if not destination:
            return get_popular_recs()
            
        # Get similar recommendations
        similar = get_similar_to_destination(destination, top_n=4)
        
        # Format recommendations with details
        recommendations = []
        for title in similar:
            details = get_destination_details(title)
            if details:
                state = details.get('state', '').lower()
                link = f"{state}.html" if state in ['kerala', 'karnataka', 'maharashtra'] else "destinations.html"
                
                recommendations.append({
                    "id": title.lower().replace(' ', '-'),
                    "title": title,
                    "description": f"Similar to {destination}",
                    "image": f"images/{abs(hash(title)) % 90 + 10}.jpg",  # Use abs() for hash value
                    "tags": details.get('tags', '').split()[:4],
                    "type": details.get('type', 'destination'),
                    "state": state,
                    "link": link
                })
        
        return jsonify({"recommendations": recommendations})
        
    except Exception as e:
        print("Similar recommendation error:", str(e))
        return jsonify({"error": "Failed to get similar recommendations", "details": str(e)}), 500

@app.route('/api/recommendations/seasonal', methods=['GET'])
def get_seasonal_recs():
    """Get seasonal recommendations"""
    try:
        # Get current season (simplified)
        month = datetime.now().month
        if 3 <= month <= 5:
            season = "spring"
        elif 6 <= month <= 8:
            season = "summer"
        elif 9 <= month <= 11:
            season = "monsoon"
        else:
            season = "winter"
            
        # Get season from request (if provided)
        req_season = request.args.get('season')
        if req_season:
            season = req_season
            
        # Get seasonal recommendations
        seasonal = get_seasonal_recommendations(season, top_n=4)
        
        # Format recommendations with details
        recommendations = []
        for title in seasonal:
            details = get_destination_details(title)
            if details:
                state = details.get('state', '').lower()
                link = f"{state}.html" if state in ['kerala', 'karnataka', 'maharashtra'] else "destinations.html"
                
                recommendations.append({
                    "id": title.lower().replace(' ', '-'),
                    "title": title,
                    "description": f"Perfect for {season}",
                    "image": f"images/{abs(hash(title)) % 90 + 10}.jpg",  # Use abs() for hash value
                    "tags": details.get('tags', '').split()[:4],
                    "type": details.get('type', 'destination'),
                    "state": state,
                    "link": link
                })
        
        return jsonify({"recommendations": recommendations, "season": season})
        
    except Exception as e:
        print("Seasonal recommendation error:", str(e))
        return jsonify({"error": "Failed to get seasonal recommendations", "details": str(e)}), 500

@app.route('/api/track/view', methods=['POST'])
def track_view():
    """Track when a user views a destination"""
    try:
        user_email = session.get('email')
        if not user_email:
            return jsonify({"error": "User not logged in"}), 401
            
        data = request.json
        destination = data.get('destination')
        if not destination:
            return jsonify({"error": "No destination provided"}), 400
            
        # Record this view
        user_activity.insert_one({
            "user_email": user_email,
            "activity_type": "view_destination",
            "destination": destination,
            "timestamp": datetime.utcnow()
        })
        
        return jsonify({"message": "View tracked successfully"})
        
    except Exception as e:
        print("View tracking error:", str(e))
        return jsonify({"error": "Failed to track view", "details": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful travel assistant."},
                {"role": "user", "content": user_msg}
            ]
        )
        bot_reply = response.choices[0].message.content.strip()
        return jsonify({"reply": bot_reply})
    except Exception as e:
        print("Chatbot error:", e)
        return jsonify({"reply": "Sorry, something went wrong."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)