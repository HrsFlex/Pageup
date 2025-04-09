# from geopy.distance import geodesic

# def compute_distance_matrix(named_locations):
#     size = len(named_locations)
#     matrix = [[0.0 for _ in range(size)] for _ in range(size)]

#     for i in range(size):
#         for j in range(i + 1, size):
#             coord1 = named_locations[i][1]
#             coord2 = named_locations[j][1]
#             dist = geodesic(coord1, coord2).km
#             matrix[i][j] = dist
#             matrix[j][i] = dist  #optimized 

#     return matrix

from geopy.distance import geodesic

def build_distance_matrix(locations):
    matrix = []
    for i in range(len(locations)):
        row = []
        for j in range(len(locations)):
            coord_i = locations[i][1]
            coord_j = locations[j][1]
            row.append(geodesic(coord_i, coord_j).km)
        matrix.append(row)
    return matrix


def compute_distance_matrix(locations):
    size = len(locations)
    matrix = [[0] * size for _ in range(size)]

    for i in range(size):
        for j in range(size):
            if i != j:
                matrix[i][j] = geodesic(locations[i][1], locations[j][1]).km
            else:
                matrix[i][j] = 0.0
    return matrix