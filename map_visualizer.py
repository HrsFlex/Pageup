
import folium #for map
import os
import webbrowser #open to new browser
from geopy.distance import geodesic  #cal distance between two points



def compute_total_distance(locations, route):
    total = 0.0
    for i in range(len(route) - 1):
        point_a = locations[route[i]]
        point_b = locations[route[i + 1]]
        total += geodesic(point_a, point_b).km
    return total


def plot_route(locations, route, total_distance):
    coords = [locations[i][1] for i in route]
    names = [locations[i][0] for i in route]

    route_map = folium.Map(location=coords[0], zoom_start=13)
    folium.PolyLine(coords, color="blue", weight=4.5, opacity=0.8).add_to(route_map)

    for idx, (name, (lat, lon)) in enumerate([locations[i] for i in route]):
        folium.Marker(
            location=(lat, lon),
            popup=f"{idx+1}. {name}",
            tooltip=f"{idx+1}. {name}",
            icon=folium.Icon(color="green" if idx == 0 else "blue", icon="info-sign")
        ).add_to(route_map)

    html = f"""
        <div style="font-size: 14px; color: black; background-color: white;
                    padding: 6px; border-radius: 8px;">
            <b>Total Distance:</b> {total_distance:.2f} km
        </div>
    """
    folium.Marker(
        location=coords[0],
        icon=folium.DivIcon(html=html)
    ).add_to(route_map)

    filename = "optimized_route_map.html"
    route_map.save(filename)
    print(f"Map saved as {filename}")
    webbrowser.open("file://" + os.path.realpath(filename))