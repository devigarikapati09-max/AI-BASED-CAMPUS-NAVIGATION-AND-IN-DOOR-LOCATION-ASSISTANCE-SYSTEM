"""
Route Finder Module
Implements Dijkstra's algorithm and A* search for finding optimal paths
within and between campus buildings.
"""
import math
import heapq
from collections import defaultdict
from campus_map import CampusMap


class RouteFinder:
    """Finds optimal routes using graph-based pathfinding algorithms."""

    def __init__(self, campus_map: CampusMap):
        self.campus = campus_map
        self.graph = {}  # adjacency list representation

    def build_graph(self, use_accessible_only=False):
        """Build a navigation graph from the campus map data."""
        self.graph = defaultdict(dict)

        for building in self.campus.buildings.values():
            if use_accessible_only and not building.is_accessible:
                continue

            for floor in building.floors.values():
                for wp_id, waypoint in floor.waypoints.items():
                    if use_accessible_only and not waypoint.is_accessible:
                        continue

                    for neighbor_id, distance in waypoint.connections:
                        self.graph[wp_id][neighbor_id] = distance
                        self.graph[neighbor_id][wp_id] = distance

                # Connect rooms to nearest waypoints
                for room_id, room in floor.rooms.items():
                    if use_accessible_only and not room.is_accessible:
                        continue
                    # Connect room to all waypoints on the same floor
                    for wp_id, waypoint in floor.waypoints.items():
                        dist = math.sqrt(
                            (room.room_id_hash() % 100 - waypoint.x) ** 2 +
                            ((room.room_id_hash() // 100) % 100 - waypoint.y) ** 2
                        )
                        self.graph[room.room_id][wp_id] = dist

        # Connect waypoints across floors (stairs/elevator)
        for building in self.campus.buildings.values():
            if use_accessible_only and not building.is_accessible:
                continue
            floors = sorted(building.floors.keys())
            for i in range(len(floors) - 1):
                # Connect stair waypoints between floors
                for wp in building.floors[floors[i]].waypoints.values():
                    if wp.waypoint_type in ('stairs', 'elevator'):
                        if use_accessible_only and not wp.is_accessible:
                            continue
                        for wp2 in building.floors[floors[i + 1]].waypoints.values():
                            if wp2.waypoint_type == wp.waypoint_type:
                                if use_accessible_only and not wp2.is_accessible:
                                    continue
                                self.graph[wp.id][wp2.id] = 5  # 5m between floors
                                self.graph[wp2.id][wp.id] = 5

        # Connect buildings (inter-building paths)
        for (b1, b2), dist in self.campus.inter_building_paths.items():
            b1_obj = self.campus.get_building(b1)
            b2_obj = self.campus.get_building(b2)
            if use_accessible_only:
                if not b1_obj.is_accessible or not b2_obj.is_accessible:
                    continue
            # Connect entrance waypoints
            for wp in b1_obj.floors[1].waypoints.values():
                if wp.waypoint_type == 'entrance':
                    for wp2 in b2_obj.floors[1].waypoints.values():
                        if wp2.waypoint_type == 'entrance':
                            self.graph[wp.id][wp2.id] = dist
                            self.graph[wp2.id][wp.id] = dist

    def dijkstra(self, start, end, accessible_only=False):
        """Dijkstra's shortest path algorithm."""
        if accessible_only:
            self.build_graph(use_accessible_only=True)

        if start not in self.graph or end not in self.graph:
            return None, float('inf')

        distances = {node: float('inf') for node in self.graph}
        distances[start] = 0
        previous = {node: None for node in self.graph}
        visited = set()
        pq = [(0, start)]

        while pq:
            current_dist, current = heapq.heappop(pq)

            if current in visited:
                continue
            visited.add(current)

            if current == end:
                break

            for neighbor, weight in self.graph[current].items():
                distance = current_dist + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))

        # Reconstruct path
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()

        return path, distances[end]

    def astar(self, start, end, accessible_only=False):
        """A* search algorithm with Euclidean distance heuristic."""
        if accessible_only:
            self.build_graph(use_accessible_only=True)

        if start not in self.graph or end not in self.graph:
            return None, float('inf')

        def heuristic(node_a, node_b):
            """Euclidean distance heuristic."""
            return math.sqrt((node_a - node_b) ** 2)

        open_set = [(0, start)]
        came_from = {}
        g_score = {node: float('inf') for node in self.graph}
        g_score[start] = 0
        f_score = {node: float('inf') for node in self.graph}
        f_score[start] = heuristic(start, end)
        closed_set = set()

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == end:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path, g_score[end]

            if current in closed_set:
                continue
            closed_set.add(current)

            for neighbor, weight in self.graph[current].items():
                if neighbor in closed_set:
                    continue
                tentative_g = g_score[current] + weight
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return None, float('inf')

    def find_nearest_waypoint(self, room_id):
        """Find the nearest waypoint to a given room."""
        for building in self.campus.buildings.values():
            for floor in building.floors.values():
                if room_id in floor.rooms:
                    room = floor.rooms[room_id]
                    nearest_wp = None
                    min_dist = float('inf')
                    for wp_id, wp in floor.waypoints.items():
                        dist = math.sqrt(
                            (room.room_id_hash() % 100 - wp.x) ** 2 +
                            ((room.room_id_hash() // 100) % 100 - wp.y) ** 2
                        )
                        if dist < min_dist:
                            min_dist = dist
                            nearest_wp = wp_id
                    return nearest_wp
        return None

    def get_route_description(self, path, start_room, end_room):
        """Generate a human-readable description of the route."""
        if not path or len(path) < 2:
            return "No route found."

        description = f"Starting from {start_room.room_number} ({start_room.room_name}).\n"
        description += f"Destination: {end_room.room_number} ({end_room.room_name}).\n\n"

        for i in range(len(path) - 1):
            current = path[i]
            next_node = path[i + 1]

            # Check if moving between floors
            for building in self.campus.buildings.values():
                for floor_num, floor in building.floors.items():
                    if current in floor.waypoints:
                        wp = floor.waypoints[current]
                        if next_node in building.floors.get(floor_num + 1, type('obj', (), {'waypoints': {}})).waypoints:
                            next_wp = building.floors[floor_num + 1].waypoints.get(next_node)
                            if next_wp and wp.waypoint_type == 'stairs':
                                description += f"Take stairs to Floor {floor_num + 1}.\n"
                            elif next_wp and wp.waypoint_type == 'elevator':
                                description += f"Take elevator to Floor {floor_num + 1}.\n"
                        break

        description += f"\nArrived at {end_room.room_number} ({end_room.room_name})."
        description += f"\nTotal distance: {self._calculate_total_distance(path):.1f} meters."
        return description

    def _calculate_total_distance(self, path):
        """Calculate total distance along a path."""
        total = 0
        for i in range(len(path) - 1):
            if path[i] in self.graph and path[i + 1] in self.graph[path[i]]:
                total += self.graph[path[i]][path[i + 1]]
            else:
                total += 10  # default distance
        return total

    def get_all_routes_from(self, start_room_id):
        """Get routes from a starting room to all other rooms."""
        routes = {}
        start_wp = self.find_nearest_waypoint(start_room_id)
        if not start_wp:
            return routes

        for building in self.campus.buildings.values():
            for floor in building.floors.values():
                for room_id, room in floor.rooms.items():
                    if room_id == start_room_id:
                        continue
                    end_wp = self.find_nearest_waypoint(room_id)
                    if end_wp:
                        path, distance = self.dijkstra(start_wp, end_wp)
                        if path and distance < float('inf'):
                            routes[room_id] = {
                                'room': room,
                                'path': path,
                                'distance': distance,
                                'building': building.name
                            }
        return routes

    def evaluate_route_quality(self, path, distance, max_floors=1):
        """Evaluate the quality of a route based on multiple criteria."""
        score = 100

        # Penalize long distances
        if distance > 500:
            score -= 30
        elif distance > 200:
            score -= 15

        # Penalize floor changes
        floor_changes = 0
        for i in range(len(path) - 1):
            for building in self.campus.buildings.values():
                for floor_num in building.floors:
                    if path[i] in building.floors[floor_num].waypoints:
                        for fn in building.floors:
                            if path[i + 1] in building.floors[fn].waypoints and fn != floor_num:
                                floor_changes += 1

        if floor_changes > max_floors:
            score -= 20 * (floor_changes - max_floors)

        return max(0, score)


# Add hash method to Room for waypoint distance calculation
def _room_id_hash(self):
    """Generate a hash from room_id for coordinate mapping."""
    return hash(self.room_id)

from campus_map import Room
Room.room_id_hash = _room_id_hash
