import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random

# Enhanced destination dataset with more information
destination_data = [
    {"title": "Kovalam Beach", "tags": "beach sea sand sunset relaxation coastal kerala", "type": "beach", "state": "kerala"},
    {"title": "Munnar", "tags": "hillstation tea plantation mountains scenic nature greenery kerala", "type": "hillstation", "state": "kerala"},
    {"title": "Hampi", "tags": "historic ruins temple architecture ancient karnataka heritage", "type": "historic", "state": "karnataka"},
    {"title": "Coorg", "tags": "coffee hillstation greenery nature adventure trekking karnataka", "type": "hillstation", "state": "karnataka"},
    {"title": "Alleppey", "tags": "backwaters boat beach houseboat relaxation kerala water", "type": "backwaters", "state": "kerala"},
    {"title": "Goa", "tags": "beach party seafood coastal nightlife water activities", "type": "beach", "state": "goa"},
    {"title": "Mysore", "tags": "palace historic cultural heritage karnataka architecture royal", "type": "historic", "state": "karnataka"},
    {"title": "Mahabaleshwar", "tags": "hillstation strawberry scenic viewpoints maharashtra mountains", "type": "hillstation", "state": "maharashtra"},
    {"title": "Fort Kochi", "tags": "historic colonial beach culture heritage kerala fishing", "type": "historic", "state": "kerala"},
    {"title": "Gateway of India", "tags": "landmark monument historic iconic maharashtra mumbai", "type": "historic", "state": "maharashtra"},
    {"title": "Marine Drive", "tags": "scenic promenade coast seafront city urban mumbai maharashtra", "type": "urban", "state": "maharashtra"},
    {"title": "Nandi Hills", "tags": "sunrise scenic trekking nature viewpoint bangalore karnataka", "type": "hillstation", "state": "karnataka"},
    {"title": "Thekkady", "tags": "wildlife sanctuary forest nature kerala boating animals", "type": "wildlife", "state": "kerala"},
    {"title": "Ajanta Caves", "tags": "caves historic ancient paintings buddhist maharashtra heritage", "type": "historic", "state": "maharashtra"},
    {"title": "Banasura Sagar Dam", "tags": "dam scenic water reservoir trekking wayanad kerala", "type": "nature", "state": "kerala"},
    {"title": "Sula Vineyards", "tags": "vineyard wine countryside relaxation nashik maharashtra", "type": "culture", "state": "maharashtra"},
    {"title": "Malpe Beach", "tags": "beach clean water sports island udupi karnataka", "type": "beach", "state": "karnataka"},
    {"title": "Lalbagh Botanical Garden", "tags": "garden botanical plants nature urban bengaluru karnataka", "type": "nature", "state": "karnataka"},
    {"title": "Padmanabhaswamy Temple", "tags": "temple historic religious architecture kerala heritage", "type": "religious", "state": "kerala"},
    {"title": "Elephanta Caves", "tags": "caves unesco heritage historic mumbai maharashtra sculpture", "type": "historic", "state": "maharashtra"}
]

# Convert to DataFrame
df = pd.DataFrame(destination_data)

# Prepare TF-IDF matrix once
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(df["tags"])
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
title_to_index = pd.Series(df.index, index=df["title"])

def get_recommendations(wishlist_titles, top_n=3):
    """
    Generate recommendations based on user's wishlist items
    """
    # Check if any wishlist titles match our dataset
    valid_titles = [title for title in wishlist_titles if title in title_to_index.index]
    
    if not valid_titles:
        # If no matches, return some popular recommendations
        return get_popular_recommendations(top_n)
    
    # Get indices of items in the wishlist
    indices = [title_to_index[title] for title in valid_titles]
    
    # Calculate similarity scores
    sim_scores = cosine_sim[indices].mean(axis=0)
    sim_scores = list(enumerate(sim_scores))
    
    # Filter out items that are already in the wishlist
    sim_scores = [s for s in sim_scores if s[0] not in indices]
    
    # Sort by similarity score
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    # Get indices of top recommendations
    top_indices = [i[0] for i in sim_scores[:top_n]]
    
    # Return recommendations
    return df["title"].iloc[top_indices].tolist()

def get_popular_recommendations(top_n=3):
    """
    Return popular destinations (could be based on view counts in a real system)
    """
    popular_indices = [0, 1, 6, 9, 12]  # Indices of popular destinations
    random.shuffle(popular_indices)
    return df["title"].iloc[popular_indices[:top_n]].tolist()

def get_recommendations_by_state(state, exclude_titles=None, top_n=3):
    """
    Get recommendations by state
    """
    if exclude_titles is None:
        exclude_titles = []
    
    # Get indices of items to exclude
    exclude_indices = [title_to_index[title] for title in exclude_titles if title in title_to_index]
    
    # Filter by state
    state_df = df[df["state"] == state.lower()]
    
    # Exclude items that are already in the wishlist
    state_df = state_df[~state_df.index.isin(exclude_indices)]
    
    if state_df.empty:
        return []
    
    # If we have fewer items than requested, return all
    if len(state_df) <= top_n:
        return state_df["title"].tolist()
    
    # Otherwise, return a random selection
    return state_df.sample(n=top_n)["title"].tolist()

def get_recommendations_by_type(type_name, exclude_titles=None, top_n=3):
    """
    Get recommendations by type (beach, hillstation, etc.)
    """
    if exclude_titles is None:
        exclude_titles = []
    
    # Get indices of items to exclude
    exclude_indices = [title_to_index[title] for title in exclude_titles if title in title_to_index]
    
    # Filter by type
    type_df = df[df["type"] == type_name.lower()]
    
    # Exclude items that are already in the wishlist
    type_df = type_df[~type_df.index.isin(exclude_indices)]
    
    if type_df.empty:
        return []
    
    # If we have fewer items than requested, return all
    if len(type_df) <= top_n:
        return type_df["title"].tolist()
    
    # Otherwise, return a random selection
    return type_df.sample(n=top_n)["title"].tolist()

def analyze_wishlist_preferences(wishlist_titles):
    """
    Analyze wishlist to determine user preferences
    """
    if not wishlist_titles:
        return {"preferred_state": None, "preferred_type": None}
    
    valid_titles = [title for title in wishlist_titles if title in title_to_index.index]
    
    if not valid_titles:
        return {"preferred_state": None, "preferred_type": None}
    
    # Get items from the wishlist that are in our dataset
    wishlist_df = df[df["title"].isin(valid_titles)]
    
    # Count state frequencies
    state_counts = wishlist_df["state"].value_counts()
    preferred_state = state_counts.idxmax() if not state_counts.empty else None
    
    # Count type frequencies
    type_counts = wishlist_df["type"].value_counts()
    preferred_type = type_counts.idxmax() if not type_counts.empty else None
    
    return {
        "preferred_state": preferred_state,
        "preferred_type": preferred_type
    }

def get_trending_recommendations(top_n=3):
    """
    In a real system, this would be based on recent view/booking trends
    Here we'll just return a randomized selection of items
    """
    return df.sample(n=min(top_n, len(df)))["title"].tolist()

def get_seasonal_recommendations(season, top_n=3):
    """
    Provide season-appropriate recommendations
    """
    season_mapping = {
        "summer": ["beach", "hillstation", "waterfall"],
        "monsoon": ["waterfall", "hillstation", "nature"],
        "winter": ["beach", "historic", "wildlife"],
        "spring": ["nature", "garden", "hillstation"]
    }
    
    if season.lower() not in season_mapping:
        return get_popular_recommendations(top_n)
    
    recommended_types = season_mapping[season.lower()]
    season_df = df[df["type"].isin(recommended_types)]
    
    if len(season_df) <= top_n:
        return season_df["title"].tolist()
    
    return season_df.sample(n=top_n)["title"].tolist()

def get_similar_to_destination(destination_title, exclude_titles=None, top_n=3):
    """
    Get destinations similar to a given destination
    """
    if exclude_titles is None:
        exclude_titles = []
    
    if destination_title not in title_to_index:
        return get_popular_recommendations(top_n)
    
    idx = title_to_index[destination_title]
    
    # Get similarity scores
    sim_scores = list(enumerate(cosine_sim[idx]))
    
    # Exclude the destination itself and items in the exclude list
    exclude_indices = [idx]
    exclude_indices.extend([title_to_index[title] for title in exclude_titles if title in title_to_index])
    
    sim_scores = [s for s in sim_scores if s[0] not in exclude_indices]
    
    # Sort by similarity
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    # Get top similar destinations
    top_indices = [i[0] for i in sim_scores[:top_n]]
    
    return df["title"].iloc[top_indices].tolist()

def get_destination_details(destination_title):
    """
    Get details for a specific destination
    """
    if destination_title not in title_to_index:
        return None
    
    idx = title_to_index[destination_title]
    destination = df.iloc[idx].to_dict()
    
    # Add similar destinations
    destination["similar"] = get_similar_to_destination(destination_title, top_n=3)
    
    return destination