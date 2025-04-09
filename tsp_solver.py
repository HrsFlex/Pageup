# from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# def solve_tsp(distance_matrix, return_to_start=True):
#     # Create routing model
#     manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
#     routing = pywrapcp.RoutingModel(manager)

#     # Distance callback function
#     def distance_callback(from_index, to_index):
#         from_node = manager.IndexToNode(from_index)
#         to_node = manager.IndexToNode(to_index)
#         return int(distance_matrix[from_node][to_node] * 1000)  # Convert km to meters

#     transit_callback_index = routing.RegisterTransitCallback(distance_callback)
#     routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

#     # Set search parameters
#     search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    
#     # First solution strategy (pick one):
#     search_parameters.first_solution_strategy = (
#         routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC  # Default
#         # routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
#         # routing_enums_pb2.FirstSolutionStrategy.CHRISTOFIDES
#     )
    
#     # Local search metaheuristic (pick one):
#     search_parameters.local_search_metaheuristic = (
#         routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH  # Best for TSP
#         # routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH
#     )
    
#     search_parameters.time_limit.seconds = 15  # Increase for larger problems
#     search_parameters.log_search = True  # Disable logging

#     # Solve the problem
#     solution = routing.SolveWithParameters(search_parameters)

#     if solution:
#         # Extract route
#         index = routing.Start(0)
#         route = []
#         while not routing.IsEnd(index):
#             route.append(manager.IndexToNode(index))
#             index = solution.Value(routing.NextVar(index))
        
#         if return_to_start:
#             route.append(manager.IndexToNode(index))

#         # Calculate true distance in km
#         total_distance = 0.0
#         for i in range(len(route) - 1):
#             total_distance += distance_matrix[route[i]][route[i + 1]]

#         return route, round(total_distance, 2)

#     return None, None

from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from geopy.distance import geodesic


def solve_tsp(distance_matrix, return_to_start=True):
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 1000)  # Convert km to meters

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = 15

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        index = routing.Start(0)
        route = []
        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))

        if return_to_start:
            route.append(manager.IndexToNode(index))

        # Total distance
        total_distance = 0.0
        for i in range(len(route) - 1):
            total_distance += distance_matrix[route[i]][route[i + 1]]

        return route, round(total_distance, 2)

    return None, None

# def solve_tsp_greedy(locations, return_to_start=True):
#     n = len(locations)
#     visited = [False] * n
#     route = [0]  # Start from first location (index 0)
#     visited[0] = True
#     current = 0

#     for _ in range(n - 1):
#         nearest = None
#         min_dist = float('inf')
#         for j in range(n):
#             if not visited[j]:
#                 dist = geodesic(locations[current][1], locations[j][1]).km
#                 if dist < min_dist:
#                     min_dist = dist
#                     nearest = j
#         route.append(nearest)
#         visited[nearest] = True
#         current = nearest

#     if return_to_start:
#         route.append(0)

    # Total distance calculation
    total_distance = 0.0
    for i in range(len(route) - 1):
        total_distance += geodesic(locations[route[i]][1], locations[route[i + 1]][1]).km

    return route, round(total_distance, 2)
