import streamlit as st
import requests
from geopy.distance import geodesic
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import folium
from streamlit_folium import st_folium, folium_static
from streamlit_extras.stylable_container import stylable_container

# Initialize session state for map persistence
if 'map_data' not in st.session_state:
    st.session_state.map_data = None
if 'routes' not in st.session_state:
    st.session_state.routes = None
if 'locations' not in st.session_state:
    st.session_state.locations = []
if 'demands' not in st.session_state:
    st.session_state.demands = []

# Configure page
st.set_page_config(
    layout="wide",
    page_title="🚍 Multi-Bus Route Planner - Jabalpur",
    page_icon=":bus:"
)

# Custom CSS for better styling
st.markdown("""
    <style>
        .stSelectbox, .stNumberInput, .stSlider {
            margin-bottom: 15px;
        }
        .stButton>button {
            width: 100%;
            padding: 10px;
            font-weight: bold;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        .css-1aumxhk {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
        }
        .success-message {
            padding: 15px;
            background-color: #d4edda;
            color: #155724;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .error-message {
            padding: 15px;
            background-color: #f8d7da;
            color: #721c24;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# App title and description
st.title("🚍 Multi-Bus Optimal Route Planner - Jabalpur")
st.markdown("""
    <div style='margin-bottom: 20px;'>
        Plan optimal bus routes across the city based on stop demands. 
        Select stops, set bus parameters, and generate the most efficient routes.
    </div>
""", unsafe_allow_html=True)

# Predefined places with additional information
predefined_places = {
    "Gyan Ganga": {
        "coords": (23.129210544390933, 79.87486749562004),
        "info": "Educational and commercial hub"
    },
    "Global College": {
        "coords": (23.20219982690002, 79.88304505674881),
        "info": "Major educational institution"
    },
    "Sea World": {
        "coords": (23.156578080577397, 79.84123457172913),
        "info": "Popular entertainment destination"
    },
    "South Avenue Mall": {
        "coords": (23.12460218938486, 79.927164220925),
        "info": "Large shopping center"
    },
    "JNKVV": {
        "coords": (23.215416062799324, 79.96091639127673),
        "info": "Agricultural university"
    },
    "IT Park": {
        "coords": (23.130691256817723, 79.88098490914587),
        "info": "Technology business park"
    }
}

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration Panel")
    
    with st.expander("📍 Add Stops", expanded=True):
        num_stops = st.slider(
            "Number of stops", 
            min_value=2, 
            max_value=len(predefined_places), 
            value=4,
            help="Select how many stops to include in the route planning"
        )
        
        st.session_state.locations = []
        st.session_state.demands = []
        
        for i in range(num_stops):
            place = st.selectbox(
                f"Select Stop {i+1}", 
                list(predefined_places.keys()), 
                key=f"place_{i}",
                help=f"Select location for stop {i+1}"
            )
            
            # Show additional info about the place
            with stylable_container(
                key=f"info_container_{i}",
                css_styles="""
                    {
                        background-color: #f0f2f6;
                        border-radius: 5px;
                        padding: 10px;
                        margin-bottom: 10px;
                        font-size: 0.8em;
                    }
                """
            ):
                st.caption(f"ℹ️ {predefined_places[place]['info']}")
            
            demand = st.number_input(
                f"Demand at {place}", 
                min_value=1, 
                max_value=100, 
                value=20,
                key=f"demand_{i}",
                help="Estimated number of passengers boarding at this stop"
            )
            
            st.session_state.locations.append((place, predefined_places[place]["coords"]))
            st.session_state.demands.append(demand)
    
    with st.expander("🚌 Vehicle Settings", expanded=True):
        num_vehicles = st.slider(
            "Number of Buses", 
            min_value=1, 
            max_value=5, 
            value=2,
            help="Total buses available for routing"
        )
        
        vehicle_capacity = st.number_input(
            "Bus Capacity", 
            min_value=10, 
            max_value=100, 
            value=50,
            help="Maximum passengers each bus can carry"
        )
    
    with st.expander("🏁 Depot Settings", expanded=True):
        if st.session_state.locations:
            depot_place = st.selectbox(
                "Depot Location (Start Point)", 
                [loc[0] for loc in st.session_state.locations],
                help="Starting and ending point for all bus routes"
            )
            depot_index = [loc[0] for loc in st.session_state.locations].index(depot_place)

# Create distance matrix function
def create_distance_matrix(locations):
    return [
        [geodesic(loc1[1], loc2[1]).km for loc2 in locations]
        for loc1 in locations
    ]

# CVRP solver function
def solve_cvrp(distance_matrix, demands, vehicle_capacity, num_vehicles, depot=0):
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicles, depot)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_idx, to_idx):
        return int(distance_matrix[manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)] * 1000)

    def demand_callback(from_idx):
        return demands[manager.IndexToNode(from_idx)]

    transit_cb = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

    demand_cb = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_cb,
        0,
        [vehicle_capacity] * num_vehicles,
        True,
        "Capacity"
    )

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.seconds = 10

    solution = routing.SolveWithParameters(search_params)

    if solution:
        routes = []
        for vehicle_id in range(num_vehicles):
            idx = routing.Start(vehicle_id)
            route = []
            while not routing.IsEnd(idx):
                route.append(manager.IndexToNode(idx))
                idx = solution.Value(routing.NextVar(idx))
            route.append(manager.IndexToNode(idx))
            routes.append(route)
        return routes

    return None

# Generate map function
def generate_map(routes, locations, depot_index):
    route_map = folium.Map(location=locations[depot_index][1], zoom_start=13, control_scale=True)
    
    # Add tile layers with proper attributions
    folium.TileLayer(
        'openstreetmap',
        name='OpenStreetMap',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    ).add_to(route_map)
    
    folium.TileLayer(
        'https://stamen-tiles-{s}.a.ssl.fastly.net/toner/{z}/{x}/{y}.png',
        name='Stamen Toner',
        attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.'
    ).add_to(route_map)
    
    folium.TileLayer(
        'cartodbpositron',
        name='CartoDB Positron',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    ).add_to(route_map)
    
    folium.LayerControl().add_to(route_map)
    
    # Add depot marker
        # Add depot marker
    folium.Marker(
        locations[depot_index][1],
        popup=f"Depot: {locations[depot_index][0]}",
        icon=folium.Icon(color='black', icon='warehouse', prefix='fa'),
        tooltip="Depot (Start/End Point)"
    ).add_to(route_map)
    
    # Route colors
    colors = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4"]
    
    for i, route in enumerate(routes):
        # Add route start marker
        folium.Marker(
            locations[route[0]][1],
            popup=f"Bus {i+1} Start: {locations[route[0]][0]}",
            icon=folium.Icon(color=colors[i % len(colors)], icon="bus", prefix="fa"),
            tooltip=f"Bus {i+1} Start"
        ).add_to(route_map)
        
        # Add route lines and stop markers
        route_points = [locations[node][1] for node in route]
        folium.PolyLine(
            route_points,
            color=colors[i % len(colors)],
            weight=4.5,
            opacity=0.8,
            tooltip=f"Bus {i+1} Route"
        ).add_to(route_map)
        
        for j in range(1, len(route)):
            folium.CircleMarker(
                location=locations[route[j]][1],
                radius=7,
                color=colors[i % len(colors)],
                fill=True,
                fill_color=colors[i % len(colors)],
                popup=f"Bus {i+1} Stop: {locations[route[j]][0]}",
                tooltip=f"Bus {i+1} Stop {j}"
            ).add_to(route_map)
    
    return route_map

# Main execution
col1, col2 = st.columns([1, 3])

with col1:
    with stylable_container(
        key="control_panel",
        css_styles="""
            {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
            }
        """
    ):
        st.subheader("Route Controls")
        
        if st.button("🚀 Optimize Routes", help="Calculate optimal routes based on current configuration"):
            if len(st.session_state.locations) > 1:
                distance_matrix = create_distance_matrix(st.session_state.locations)
                st.session_state.routes = solve_cvrp(
                    distance_matrix,
                    st.session_state.demands,
                    vehicle_capacity,
                    num_vehicles,
                    depot=depot_index
                )
                
                if st.session_state.routes:
                    st.session_state.map_data = generate_map(
                        st.session_state.routes,
                        st.session_state.locations,
                        depot_index
                    )
                    st.success("Optimal routes calculated successfully!")
                else:
                    st.error("Failed to compute optimal routes. Try adjusting vehicle count or capacity.")
            else:
                st.warning("Please add at least 2 stops to calculate routes.")

        if st.button("🔄 Reset Map", help="Clear the current map display"):
            st.session_state.map_data = None
            st.session_state.routes = None
            st.rerun()

    if st.session_state.routes:
        with stylable_container(
            key="results_panel",
            css_styles="""
                {
                    background-color: #f8f9fa;
                    border-radius: 10px;
                    padding: 15px;
                }
            """
        ):
            st.subheader("Route Details")
            for i, route in enumerate(st.session_state.routes):
                with st.expander(f"🚌 Bus {i+1} Route", expanded=(i == 0)):
                    st.write(f"**Capacity used:** {sum(st.session_state.demands[node] for node in route[1:-1])}/{vehicle_capacity}")
                    st.write("**Stops:**")
                    for j, node in enumerate(route):
                        if j == 0 or j == len(route)-1:
                            st.write(f"🏁 {st.session_state.locations[node][0]} (Depot)")
                        else:
                            st.write(f"📍 {st.session_state.locations[node][0]} (Demand: {st.session_state.demands[node]})")

with col2:
    st.subheader("Route Visualization")
    
    if st.session_state.map_data:
        # Use folium_static for persistent map display
        folium_static(st.session_state.map_data, width=800, height=600)
    else:
        # Show default map with all locations when no routes are calculated
        if st.session_state.locations:
            default_map = folium.Map(location=st.session_state.locations[0][1], zoom_start=12)
            for loc in st.session_state.locations:
                folium.Marker(
                    loc[1],
                    popup=loc[0],
                    icon=folium.Icon(color='gray', icon='map-marker')
                ).add_to(default_map)
            folium_static(default_map, width=800, height=600)
        else:
            st.info("Add stops in the sidebar to begin route planning")

# Footer
st.markdown("""
    <div style='margin-top: 30px; text-align: center; color: #666; font-size: 0.9em;'>
        <hr>
        <p>Multi-Bus Optimal Route Planner | Jabalpur Transport Authority</p>
    </div>
""", unsafe_allow_html=True)