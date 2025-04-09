import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.distance import geodesic

# Configure page
st.set_page_config(page_title="📍 Route Optimizer", layout="wide")

# Custom CSS for better appearance
st.markdown("""
    <style>
        .stButton>button {
            background-color: #1F4E79;
            color: white;
            border-radius: 5px;
            padding: 0.5rem 1rem;
        }
        .stTextInput>div>div>input {
            border-radius: 5px;
            padding: 0.5rem;
        }
        .stTextArea textarea {
            border-radius: 5px;
            min-height: 150px;
        }
        .stMarkdown h1 {
            border-bottom: 2px solid #1F4E79;
            padding-bottom: 10px;
        }
        .place-card {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #1F4E79;
        }
        .tab-container {
            margin-top: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 style='text-align: center; color: #1F4E79;'>📍 Jabalpur Route Optimizer</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: grey;'>Get the shortest route with just place names!</h4>", unsafe_allow_html=True)

# Sidebar configuration
st.sidebar.header("➕ Add Places")

# Initialize session state
if "places" not in st.session_state:
    st.session_state["places"] = []

if "multi_places_input" not in st.session_state:
    st.session_state.multi_places_input = ""

if "example_loaded" not in st.session_state:
    st.session_state.example_loaded = False

# Enhanced geocoder with rate limiting and caching
@st.cache_data(ttl=3600, show_spinner=False)
def get_lat_lon(place):
    # Try Nominatim first (free but requires attribution)
    nominatim_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': place + ", Jabalpur",
        'format': 'json',
        'limit': 1,
        'countrycodes': 'in'
    }
    headers = {'User-Agent': 'JabalpurRoutePlanner/1.0'}
    
    try:
        response = requests.get(nominatim_url, params=params, headers=headers)
        if response.ok:
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
        
        # If Nominatim fails, try OpenCage as fallback
        opencage_key = "32d1e78b3e2848999a5947c8894cfe31"  # Replace with your actual key
        if opencage_key:
            oc_url = "https://api.opencagedata.com/geocode/v1/json"
            oc_params = {
                'q': place + ", Jabalpur, India",
                'key': opencage_key,
                'limit': 1,
                'no_annotations': 1
            }
            oc_response = requests.get(oc_url, params=oc_params)
            if oc_response.ok:
                results = oc_response.json().get("results", [])
                if results:
                    coords = results[0]["geometry"]
                    return coords["lat"], coords["lng"]
        
        return None, None
    
    except Exception as e:
        st.sidebar.error(f"Geocoding error: {str(e)}")
        return None, None
    
tab1, tab2 = st.sidebar.tabs(["Single Location", "Multiple Locations"])

# Single location input
with tab1:
    single_place = st.text_input("Enter a place (e.g., Apex Hospital, Jabalpur)", 
                               key="single_place_input",
                               help="Be as specific as possible for better results")
    
    if st.button("Add Single Place", key="add_single_button"):
        if single_place:
            with st.spinner(f"Locating {single_place}..."):
                latlon = get_lat_lon(single_place)
            
            if latlon[0] is not None:
                # Check for duplicates
                existing_places = [p[0].lower() for p in st.session_state["places"]]
                if single_place.lower() not in existing_places:
                    st.session_state["places"].append((single_place, latlon))
                    st.success(f"✅ {single_place} added!")
                else:
                    st.warning(f"⚠️ {single_place} is already in the list")
            else:
                st.error("⚠️ Couldn't locate the place. Try being more specific (e.g., include landmarks).")

# Multiple locations input
with tab2:
    example_locations = """Apex Hospital, Jabalpur
Rani Durgavati Museum
Dumna Airport
Gwarighat
Sangram Sagar Lake
Madan Mahal Fort
Jabalpur Engineering College
Russel Chowk"""
    
    multi_places = st.text_area(
        "Enter multiple places (one per line)",
        value=example_locations if st.session_state.example_loaded else st.session_state.multi_places_input,
        placeholder="Apex Hospital, Jabalpur\nRani Durgavati Museum\nDumna Airport\n...",
        help="Enter one place per line. Be specific for better results.",
        key="multi_places_textarea"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Multiple Places", key="add_multiple_button"):
            if multi_places:
                places_list = [p.strip() for p in multi_places.split('\n') if p.strip()]
                success_count = 0
                
                with st.spinner(f"Processing {len(places_list)} places..."):
                    for place in places_list:
                        latlon = get_lat_lon(place)
                        if latlon[0] is not None:
                            # Check for duplicates
                            existing_places = [p[0].lower() for p in st.session_state["places"]]
                            if place.lower() not in existing_places:
                                st.session_state["places"].append((place, latlon))
                                success_count += 1
                
                if success_count > 0:
                    st.success(f"✅ Added {success_count} new places!")
                    if success_count < len(places_list):
                        st.warning(f"Couldn't add {len(places_list) - success_count} places (duplicates or not found)")
                else:
                    st.error("⚠️ Couldn't add any places. Please check your input.")
    
    with col2:
        if st.button("Load Example", key="load_example_button"):
            st.session_state.example_loaded = True
            st.session_state.multi_places_input = example_locations
            st.rerun()

# Display current places list
if st.session_state["places"]:
    st.subheader("📍 Selected Places")
    cols = st.columns([3, 2, 1])
    cols[0].markdown("**Place Name**")
    cols[1].markdown("**Coordinates**")
    cols[2].markdown("**Action**")
    
    for i, (name, coords) in enumerate(st.session_state["places"]):
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(name)
        col2.code(f"{coords[0]:.9f}, {coords[1]:.9f}")
        
        # Add delete button for each place
        if col3.button("❌", key=f"del_{i}"):
            del st.session_state["places"][i]
            st.rerun()
else:
    st.info("ℹ️ Add at least 2 places to begin route optimization")

from geopy.distance import geodesic
import itertools

def total_distance(route, locations):
    dist = 0
    for i in range(len(route) - 1):
        dist += geodesic(locations[route[i]][1], locations[route[i+1]][1]).km
    return dist

def two_opt(route, locations):
    best = route
    improved = True
    while improved:
        improved = False
        for i in range(1, len(route) - 2):
            for j in range(i+1, len(route) - 1):
                if j - i == 1: continue
                new_route = route[:]
                new_route[i:j] = reversed(route[i:j])
                if total_distance(new_route, locations) < total_distance(best, locations):
                    best = new_route
                    improved = True
        route = best
    return best

def solve_tsp(locations):
    if len(locations) < 2:
        return []
    
    # Greedy initial route
    route = [0]
    unvisited = set(range(1, len(locations)))
    while unvisited:
        last = route[-1]
        nearest = min(unvisited, key=lambda x: geodesic(locations[last][1], locations[x][1]).km)
        route.append(nearest)
        unvisited.remove(nearest)
    
    route.append(0)  # Return to start

    # Improve route using 2-opt
    optimized_route = two_opt(route, locations)
    return optimized_route

if st.button("📍 Optimize Route", type="primary", key="optimize_button"):
    if len(st.session_state["places"]) < 2:
        st.warning("Please add at least 2 places to optimize a route")
    else:
        with st.spinner("Calculating optimal route..."):
            locations = st.session_state["places"]
            route = solve_tsp(locations)
            st.session_state["route"] = route
            st.session_state["optimized"] = True
            st.success("Route optimized successfully!")


# Map display
if "route" in st.session_state and "places" in st.session_state and st.session_state.get("optimized", False):
    route = st.session_state["route"]
    locations = st.session_state["places"]
    
    if route and all(i < len(locations) for i in route):
        # Get coordinates and names in route order
        coords = [locations[i][1] for i in route]
        names = [locations[i][0] for i in route]
        
        # Calculate total distance
        total_km = sum(geodesic(coords[i], coords[i+1]).km for i in range(len(coords)-1))
        
        # Create map centered on the first location
        route_map = folium.Map(
            location=coords[0],
            zoom_start=13,
            tiles="cartodbpositron"
        )
        
        # Add polyline for the route
        folium.PolyLine(
            coords,
            color="#1F4E79",
            weight=5,
            opacity=0.8,
            tooltip="Optimized Route"
        ).add_to(route_map)
        
        # Add markers with numbering
        for idx, i in enumerate(route):
            name, (lat, lon) = locations[i]
            folium.Marker(
                location=(lat, lon),
                popup=f"<b>{idx + 1}. {name}</b>",
                tooltip=f"{idx + 1}. {name}",
                icon=folium.Icon(
                    color="green" if idx == 0 else "blue",
                    icon="info-sign" if idx == 0 else "map-marker",
                    prefix="fa"
                )
            ).add_to(route_map)
        
        # Display route info
        st.subheader("🗺️ Optimized Route")
        
        # Show route steps
        st.markdown("**Route Order:**")
        for i, stop_idx in enumerate(route):
            st.write(f"{i+1}. {locations[stop_idx][0]}")
        
        # Display total distance
        st.metric("Total Distance", f"{total_km:.2f} km")
        
        # Show the map
        st_folium(route_map, width=1200, height=600, returned_objects=[])
    else:
        st.error("Invalid route generated. Please try optimizing again.")

# Clear all button
if st.sidebar.button("🧹 Clear All", type="secondary", key="clear_all_button"):
    st.session_state["places"] = []
    st.session_state.pop("route", None)
    st.session_state.pop("optimized", None)
    st.session_state.multi_places_input = ""
    st.session_state.example_loaded = False
    st.sidebar.success("All places cleared!")
    st.rerun()

# Add attribution and instructions
st.sidebar.markdown("---")
st.sidebar.markdown("**Instructions:**")
st.sidebar.markdown("1. Add at least 2 places")
st.sidebar.markdown("2. Click 'Optimize Route'")
st.sidebar.markdown("3. View the shortest path")
st.sidebar.markdown("---")
st.sidebar.markdown("© 2023 Jabalpur Route Optimizer")
st.sidebar.markdown("*Uses OpenStreetMap and OpenCage data*")

