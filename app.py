"""
Main Flask Application
AI-Based Campus Navigation and Indoor Location Assistance System
"""
from flask import Flask, render_template, request, jsonify
from campus_map import CampusMap, create_sample_campus
from route_finder import RouteFinder
from indoor_positioning import IndoorPositioning
from accessibility_service import AccessibilityService, NotificationService
from analytics_service import generate_all_charts

app = Flask(__name__)

# Initialize campus data
campus = create_sample_campus()
finder = RouteFinder(campus)
finder.build_graph()
positioning = IndoorPositioning(campus)
positioning.create_wifi_fingerprint_database()
accessibility = AccessibilityService(campus)
notifier = NotificationService()


@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search_rooms():
    """Search for rooms on campus."""
    data = request.get_json()
    query = data.get('query', '')
    room_type = data.get('room_type', None)
    building_id = data.get('building_id', None)

    results = campus.search_rooms(query, room_type, building_id)
    room_list = []
    for room in results:
        building = campus.get_building(room.building_id)
        room_list.append({
            'room_id': room.room_id,
            'room_number': room.room_number,
            'room_name': room.room_name,
            'room_type': room.room_type,
            'floor': room.floor_number,
            'building': building.name,
            'building_code': building.code,
            'capacity': room.capacity,
            'is_accessible': room.is_accessible
        })
    return jsonify({'rooms': room_list, 'total': len(room_list)})


@app.route('/locate', methods=['POST'])
def locate_user():
    """Determine user location using indoor positioning."""
    data = request.get_json()
    method = data.get('method', 'wifi')

    if method == 'wifi':
        readings = data.get('wifi_signals', {})
        result, confidence = positioning.position_by_wifi(readings)
    elif method == 'qr':
        qr_code = data.get('qr_code', '')
        result, confidence = positioning.position_by_qr_code(qr_code)
    elif method == 'beacon':
        beacon_data = data.get('beacon_signals', {})
        result, confidence = positioning.position_by_beacon(beacon_data)
    else:
        return jsonify({'error': 'Invalid positioning method'}), 400

    if result:
        return jsonify({
            'location': result,
            'confidence': confidence,
            'method': method
        })
    return jsonify({'error': 'Location could not be determined'}), 404


@app.route('/navigate', methods=['POST'])
def navigate():
    """Get navigation route between two rooms."""
    data = request.get_json()
    start_room = data.get('start_room', '')
    end_room = data.get('end_room', '')
    accessible_only = data.get('accessible_only', False)

    # Find waypoints for rooms
    start_wp = finder.find_nearest_waypoint(start_room)
    end_wp = finder.find_nearest_waypoint(end_room)

    if not start_wp or not end_wp:
        return jsonify({'error': 'Room not found'}), 404

    if accessible_only:
        path, distance = finder.dijkstra(start_wp, end_wp, accessible_only=True)
    else:
        path, distance = finder.dijkstra(start_wp, end_wp)

    if path:
        # Find room names
        start_room_obj = None
        end_room_obj = None
        for building in campus.buildings.values():
            for floor in building.floors.values():
                if start_room in floor.rooms:
                    start_room_obj = floor.rooms[start_room]
                if end_room in floor.rooms:
                    end_room_obj = floor.rooms[end_room]

        description = finder.get_route_description(
            path, start_room_obj or type('obj', (), {'room_number': start_room, 'room_name': 'Unknown'})(),
            end_room_obj or type('obj', (), {'room_number': end_room, 'room_name': 'Unknown'})()
        )

        return jsonify({
            'path': path,
            'distance': round(distance, 1),
            'description': description,
            'accessible': accessible_only
        })

    return jsonify({'error': 'No route found'}), 404


@app.route('/buildings', methods=['GET'])
def get_buildings():
    """Get all buildings with details."""
    buildings = []
    for b in campus.buildings.values():
        buildings.append({
            'building_id': b.building_id,
            'name': b.name,
            'code': b.code,
            'floors': len(b.floors),
            'is_accessible': b.is_accessible,
            'total_rooms': len(b.get_all_rooms())
        })
    return jsonify({'buildings': buildings})


@app.route('/rooms', methods=['GET'])
def get_all_rooms():
    """Get all rooms on campus."""
    rooms = []
    for building in campus.buildings.values():
        for room in building.get_all_rooms():
            rooms.append({
                'room_id': room.room_id,
                'room_number': room.room_number,
                'room_name': room.room_name,
                'room_type': room.room_type,
                'floor': room.floor_number,
                'building': building.name,
                'capacity': room.capacity,
                'is_accessible': room.is_accessible
            })
    return jsonify({'rooms': rooms, 'total': len(rooms)})


@app.route('/statistics', methods=['GET'])
def get_statistics():
    """Get campus statistics."""
    stats = campus.get_statistics()
    pos_stats = positioning.get_positioning_statistics()
    return jsonify({
        'campus': stats,
        'positioning': pos_stats
    })


@app.route('/accessibility/<building_id>', methods=['GET'])
def check_accessibility(building_id):
    """Check accessibility of a building."""
    result = accessibility.check_building_accessibility(building_id)
    if result:
        return jsonify(result)
    return jsonify({'error': 'Building not found'}), 404


@app.route('/notifications/send', methods=['POST'])
def send_notification():
    """Send a notification to a user."""
    data = request.get_json()
    user_id = data.get('user_id', '')
    message = data.get('message', '')
    notif_type = data.get('type', 'info')
    notification = notifier.send_notification(user_id, message, notif_type)
    return jsonify(notification)


@app.route('/notifications/<user_id>', methods=['GET'])
def get_notifications(user_id):
    """Get notifications for a user."""
    notifications = notifier.get_notifications(user_id)
    return jsonify({'notifications': notifications, 'total': len(notifications)})


@app.route('/analytics', methods=['GET'])
def generate_analytics():
    """Generate analytical charts."""
    accuracy_data = {'wifi_fingerprinting': 85.5, 'qr_code': 100.0, 'bluetooth_beacon': 78.3}
    notification_stats = notifier.get_notification_statistics()
    charts = generate_all_charts(campus, accuracy_data, notification_stats, 'reports')
    return jsonify({'charts': charts, 'status': 'generated'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
