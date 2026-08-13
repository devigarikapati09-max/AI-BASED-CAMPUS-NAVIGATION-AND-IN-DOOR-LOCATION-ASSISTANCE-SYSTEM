"""
Campus Map Data Model
Defines buildings, floors, rooms, waypoints, and connectivity for indoor navigation.
"""
import json
import os


class Building:
    """Represents a building on campus."""

    def __init__(self, building_id, name, code, floors, is_accessible=True):
        self.building_id = building_id
        self.name = name
        self.code = code
        self.floors = floors  # dict: floor_number -> Floor object
        self.is_accessible = is_accessible
        self.x_coord = 0  # campus grid coordinate
        self.y_coord = 0  # campus grid coordinate

    def get_all_rooms(self):
        """Get all rooms across all floors."""
        rooms = []
        for floor in self.floors.values():
            rooms.extend(floor.rooms.values())
        return rooms

    def get_floor(self, floor_number):
        """Get a specific floor."""
        return self.floors.get(floor_number)

    def to_dict(self):
        return {
            'building_id': self.building_id,
            'name': self.name,
            'code': self.code,
            'floors': list(self.floors.keys()),
            'is_accessible': self.is_accessible
        }


class Floor:
    """Represents a floor within a building."""

    def __init__(self, floor_number, building_id):
        self.floor_number = floor_number
        self.building_id = building_id
        self.rooms = {}  # room_id -> Room object
        self.waypoints = {}  # waypoint_id -> Waypoint object
        self.connections = []  # connections to other floors via stairs/elevators

    def add_room(self, room):
        self.rooms[room.room_id] = room

    def add_waypoint(self, waypoint):
        self.waypoints[waypoint.id] = waypoint


class Room:
    """Represents a room (classroom, lab, office, etc.)."""

    def __init__(self, room_id, room_number, room_name, room_type,
                 floor_number, building_id, capacity=0,
                 has_projector=False, has_ac=True, is_accessible=True):
        self.room_id = room_id
        self.room_number = room_number
        self.room_name = room_name
        self.room_type = room_type  # 'classroom', 'lab', 'office', 'seminar', 'library'
        self.floor_number = floor_number
        self.building_id = building_id
        self.capacity = capacity
        self.has_projector = has_projector
        self.has_ac = has_ac
        self.is_accessible = is_accessible
        self.description = ""
        self.faculty = ""

    def to_dict(self):
        return {
            'room_id': self.room_id,
            'room_number': self.room_number,
            'room_name': self.room_name,
            'room_type': self.room_type,
            'floor_number': self.floor_number,
            'building_id': self.building_id,
            'capacity': self.capacity,
            'has_projector': self.has_projector,
            'has_ac': self.has_ac,
            'is_accessible': self.is_accessible
        }


class Waypoint:
    """Represents a navigation waypoint (corridor junction, entrance, etc.)."""

    def __init__(self, id, x, y, floor_number, building_id,
                 waypoint_type='corridor', is_accessible=True):
        self.id = id
        self.x = x
        self.y = y
        self.floor_number = floor_number
        self.building_id = building_id
        self.waypoint_type = waypoint_type  # 'corridor', 'entrance', 'stairs', 'elevator'
        self.is_accessible = is_accessible
        self.connections = []  # list of (neighbor_id, distance)

    def add_connection(self, neighbor_id, distance):
        self.connections.append((neighbor_id, distance))

    def to_dict(self):
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'floor_number': self.floor_number,
            'building_id': self.building_id,
            'waypoint_type': self.waypoint_type
        }


class CampusMap:
    """The complete campus map with all buildings and their navigation data."""

    def __init__(self):
        self.buildings = {}  # building_id -> Building
        self.inter_building_paths = {}  # (building1_id, building2_id) -> distance

    def add_building(self, building):
        self.buildings[building.building_id] = building

    def add_inter_building_path(self, building1_id, building2_id, distance):
        self.inter_building_paths[(building1_id, building2_id)] = distance
        self.inter_building_paths[(building2_id, building1_id)] = distance

    def get_building(self, building_id):
        return self.buildings.get(building_id)

    def search_rooms(self, query, room_type=None, building_id=None):
        """Search for rooms by name or room number."""
        results = []
        query_lower = query.lower()
        for building in self.buildings.values():
            if building_id and building.building_id != building_id:
                continue
            for room in building.get_all_rooms():
                if query_lower in room.room_number.lower() or \
                   query_lower in room.room_name.lower():
                    if room_type and room.room_type != room_type:
                        continue
                    results.append(room)
        return results

    def get_accessible_buildings(self):
        """Get all buildings that are wheelchair accessible."""
        return [b for b in self.buildings.values() if b.is_accessible]

    def get_room_types(self):
        """Get all unique room types."""
        types = set()
        for building in self.buildings.values():
            for room in building.get_all_rooms():
                types.add(room.room_type)
        return types

    def get_statistics(self):
        """Get campus-wide statistics."""
        total_buildings = len(self.buildings)
        total_rooms = sum(len(b.get_all_rooms()) for b in self.buildings.values())
        total_floors = sum(len(b.floors) for b in self.buildings.values())
        accessible_buildings = sum(1 for b in self.buildings.values() if b.is_accessible)
        room_type_counts = {}
        for building in self.buildings.values():
            for room in building.get_all_rooms():
                room_type_counts[room.room_type] = room_type_counts.get(room.room_type, 0) + 1

        return {
            'total_buildings': total_buildings,
            'total_rooms': total_rooms,
            'total_floors': total_floors,
            'accessible_buildings': accessible_buildings,
            'room_type_distribution': room_type_counts
        }


def create_sample_campus():
    """Create a sample campus with multiple buildings for testing."""
    campus = CampusMap()

    # Building 1: Academic Block A
    b1 = Building('B1', 'Academic Block A', 'ABA', {1: Floor(1, 'B1'), 2: Floor(2, 'B1'), 3: Floor(3, 'B1')})
    b1.x_coord, b1.y_coord = 100, 200

    # Floor 1 rooms
    rooms_f1 = [
        Room('R101', '101', 'Physics Lab', 'lab', 1, 'B1', 40, True, True),
        Room('R102', '102', 'Chemistry Lab', 'lab', 1, 'B1', 35, True, True),
        Room('R103', '103', 'Classroom A', 'classroom', 1, 'B1', 60, True, True),
        Room('R104', '104', 'Classroom B', 'classroom', 1, 'B1', 50, True, True),
        Room('R105', '105', 'Faculty Office', 'office', 1, 'B1', 2, False, True),
    ]
    for r in rooms_f1:
        b1.floors[1].add_room(r)

    # Floor 2 rooms
    rooms_f2 = [
        Room('R201', '201', 'Computer Lab', 'lab', 2, 'B1', 45, True, True),
        Room('R202', '202', 'Electronics Lab', 'lab', 2, 'B1', 30, True, True),
        Room('R203', '203', 'Mathematics Room', 'classroom', 2, 'B1', 55, True, True),
        Room('R204', '204', 'Seminar Hall', 'seminar', 2, 'B1', 100, True, True),
    ]
    for r in rooms_f2:
        b1.floors[2].add_room(r)

    # Floor 3 rooms
    rooms_f3 = [
        Room('R301', '301', 'Library Reading Room', 'library', 3, 'B1', 80, False, True),
        Room('R302', '302', 'Faculty Cabin', 'office', 3, 'B1', 3, False, True),
        Room('R303', '303', 'Conference Room', 'seminar', 3, 'B1', 40, True, True),
    ]
    for r in rooms_f3:
        b1.floors[3].add_room(r)

    # Waypoints for Building 1
    wp_f1 = [
        Waypoint('WP_B1_F1_1', 10, 10, 1, 'B1', 'entrance'),
        Waypoint('WP_B1_F1_2', 30, 20, 1, 'B1', 'corridor'),
        Waypoint('WP_B1_F1_3', 50, 15, 1, 'B1', 'corridor'),
        Waypoint('WP_B1_F1_4', 70, 25, 1, 'B1', 'corridor'),
        Waypoint('WP_B1_F1_5', 90, 30, 1, 'B1', 'stairs'),
    ]
    for wp in wp_f1:
        b1.floors[1].add_waypoint(wp)

    wp_f2 = [
        Waypoint('WP_B1_F2_1', 10, 10, 2, 'B1', 'corridor'),
        Waypoint('WP_B1_F2_2', 30, 20, 2, 'B1', 'corridor'),
        Waypoint('WP_B1_F2_3', 50, 15, 2, 'B1', 'corridor'),
        Waypoint('WP_B1_F2_4', 70, 25, 2, 'B1', 'stairs'),
    ]
    for wp in wp_f2:
        b1.floors[2].add_waypoint(wp)

    campus.add_building(b1)

    # Building 2: Engineering Block
    b2 = Building('B2', 'Engineering Block', 'ENG', {1: Floor(1, 'B2'), 2: Floor(2, 'B2')})
    b2.x_coord, b2.y_coord = 300, 200

    rooms_b2_f1 = [
        Room('R2101', '101', 'Mechanical Lab', 'lab', 1, 'B2', 35, True, True),
        Room('R2102', '102', 'Workshop', 'lab', 1, 'B2', 50, True, True),
        Room('R2103', '103', 'Drawing Hall', 'classroom', 1, 'B2', 60, True, True),
        Room('R2104', '104', 'Material Testing Lab', 'lab', 1, 'B2', 25, True, True),
    ]
    for r in rooms_b2_f1:
        b2.floors[1].add_room(r)

    rooms_b2_f2 = [
        Room('R2201', '201', 'Civil Engineering Lab', 'lab', 2, 'B2', 30, True, True),
        Room('R2202', '202', 'Surveying Lab', 'lab', 2, 'B2', 20, True, True),
        Room('R2203', '203', 'Environmental Lab', 'lab', 2, 'B2', 25, True, True),
        Room('R2204', '204', 'Project Room', 'seminar', 2, 'B2', 40, True, True),
    ]
    for r in rooms_b2_f2:
        b2.floors[2].add_room(r)

    campus.add_building(b2)

    # Building 3: Science Block
    b3 = Building('B3', 'Science Block', 'SCI', {1: Floor(1, 'B3'), 2: Floor(2, 'B3')}, is_accessible=False)
    b3.x_coord, b3.y_coord = 500, 150

    rooms_b3_f1 = [
        Room('R3101', '101', 'Biology Lab', 'lab', 1, 'B3', 30, True, True),
        Room('R3102', '102', 'Zoology Lab', 'lab', 1, 'B3', 25, True, True),
        Room('R3103', '103', 'Botany Lab', 'lab', 1, 'B3', 25, True, True),
        Room('R3104', '104', 'Science Classroom', 'classroom', 1, 'B3', 50, True, True),
    ]
    for r in rooms_b3_f1:
        b3.floors[1].add_room(r)

    rooms_b3_f2 = [
        Room('R3201', '201', 'Research Lab', 'lab', 2, 'B3', 15, True, True),
        Room('R3202', '202', 'Microscopy Room', 'lab', 2, 'B3', 10, True, True),
        Room('R3203', '203', 'Faculty Office', 'office', 2, 'B3', 5, False, True),
    ]
    for r in rooms_b3_f2:
        b3.floors[2].add_room(r)

    campus.add_building(b3)

    # Building 4: Admin Block
    b4 = Building('B4', 'Administrative Block', 'ADM', {1: Floor(1, 'B4')})
    b4.x_coord, b4.y_coord = 100, 400

    rooms_b4_f1 = [
        Room('R4101', '101', 'Principal Office', 'office', 1, 'B4', 2, False, True),
        Room('R4102', '102', 'Examination Cell', 'office', 1, 'B4', 10, False, True),
        Room('R4103', '103', 'Accounts Office', 'office', 1, 'B4', 8, False, True),
        Room('R4104', '104', 'Student Service Center', 'office', 1, 'B4', 15, False, True),
    ]
    for r in rooms_b4_f1:
        b4.floors[1].add_room(r)

    campus.add_building(b4)

    # Building 5: Library
    b5 = Building('B5', 'Central Library', 'LIB', {1: Floor(1, 'B5'), 2: Floor(2, 'B5')})
    b5.x_coord, b5.y_coord = 300, 400

    rooms_b5_f1 = [
        Room('R5101', '101', 'Circulation Desk', 'office', 1, 'B5', 5, False, True),
        Room('R5102', '102', 'Reference Section', 'library', 1, 'B5', 100, False, True),
        Room('R5103', '103', 'Digital Resource Center', 'library', 1, 'B5', 50, True, True),
    ]
    for r in rooms_b5_f1:
        b5.floors[1].add_room(r)

    rooms_b5_f2 = [
        Room('R5201', '201', 'Periodicals Section', 'library', 2, 'B5', 40, False, True),
        Room('R5202', '202', 'Thesis Repository', 'library', 2, 'B5', 20, False, True),
        Room('R5203', '203', 'Study Hall', 'library', 2, 'B5', 60, True, True),
    ]
    for r in rooms_b5_f2:
        b5.floors[2].add_room(r)

    campus.add_building(b5)

    # Inter-building paths (distances in meters)
    campus.add_inter_building_path('B1', 'B2', 200)
    campus.add_inter_building_path('B1', 'B3', 400)
    campus.add_inter_building_path('B1', 'B4', 200)
    campus.add_inter_building_path('B1', 'B5', 300)
    campus.add_inter_building_path('B2', 'B3', 200)
    campus.add_inter_building_path('B2', 'B4', 350)
    campus.add_inter_building_path('B2', 'B5', 200)
    campus.add_inter_building_path('B3', 'B4', 500)
    campus.add_inter_building_path('B3', 'B5', 300)
    campus.add_inter_building_path('B4', 'B5', 200)

    return campus


def save_campus_to_json(campus, filepath='campus_data.json'):
    """Save campus data to JSON file."""
    data = {
        'buildings': {},
        'inter_building_paths': {}
    }
    for bid, b in campus.buildings.items():
        data['buildings'][bid] = {
            'name': b.name,
            'code': b.code,
            'x_coord': b.x_coord,
            'y_coord': b.y_coord,
            'is_accessible': b.is_accessible,
            'floors': {}
        }
        for fid, floor in b.floors.items():
            data['buildings'][bid]['floors'][str(fid)] = {
                'rooms': {rid: r.to_dict() for rid, r in floor.rooms.items()},
                'waypoints': {wid: wp.to_dict() for wid, wp in floor.waypoints.items()}
            }
    for key, dist in campus.inter_building_paths.items():
        if key[0] < key[1]:  # Avoid duplicates
            data['inter_building_paths'][f"{key[0]}-{key[1]}"] = dist

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    return filepath


if __name__ == '__main__':
    campus = create_sample_campus()
    stats = campus.get_statistics()
    print("Campus Statistics:")
    print(f"  Total Buildings: {stats['total_buildings']}")
    print(f"  Total Rooms: {stats['total_rooms']}")
    print(f"  Total Floors: {stats['total_floors']}")
    print(f"  Accessible Buildings: {stats['accessible_buildings']}")
    print(f"  Room Type Distribution: {stats['room_type_distribution']}")

    # Search test
    results = campus.search_rooms('lab')
    print(f"\nRooms matching 'lab': {len(results)}")
    for r in results:
        print(f"  {r.room_number}: {r.room_name} ({r.room_type}) in {campus.buildings[r.building_id].name}")

    # Save to JSON
    save_campus_to_json(campus, 'campus_data.json')
    print("\nCampus data saved to campus_data.json")
