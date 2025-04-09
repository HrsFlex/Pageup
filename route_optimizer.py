

from sample_input import locations
from distance_utils import compute_distance_matrix
from tsp_solver import solve_tsp
# from tsp_solver import solve_tsp_greedy
from map_visualizer import plot_route

# Set this to False if you do NOT want to return to the origin
return_to_start = True

def print_directions(locations, route):
    print(" Delivery Route Directions:")
    for i in range(len(route)):
        name, (lat, lon) = locations[route[i]]
        print(f"{i+1}. {name} - ({lat:.6f}, {lon:.6f})")


def main():
    distance_matrix = compute_distance_matrix(locations)

    distance_matrix = compute_distance_matrix(locations)

    route, total_distance = solve_tsp(distance_matrix)

    

    # route, total_km = solve_tsp_greedy(locations)

    # print("Greedy Route:")
    # for i in route:
    #     print(f"{i}: {locations[i][0]}")
    # print(f"\nTotal Distance (Greedy): {total_km} km")
    if route:
        print("Optimized route (index order):", route)
        print_directions(locations, route)
        # plot_route(locations, route, total_km)
        plot_route(locations, route, total_distance)
    else:
        print("No solution found.")
    print("Final Route:")
    for i in route:
        print(f"{i}: {locations[i][0]}")




if __name__ == "__main__":
    main()
