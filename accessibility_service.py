"""
Accessibility and Notification Service Module
Provides accessibility features for differently abled users and
real-time notification system for campus navigation.
"""
import time
import threading
from collections import defaultdict
from campus_map import CampusMap


class AccessibilityService:
    """Provides accessibility features for differently abled users."""

    def __init__(self, campus_map: CampusMap):
        self.campus = campus_map
        self.accessible_routes = {}
        self.voice_guidance = True
        self.high_contrast = False
        self.text_to_speech = True

    def get_accessible_route(self, start_room_id, end_room_id):
        """Find a route that avoids stairs and uses elevators only."""
        accessible_buildings = []
        for building in self.campus.buildings.values():
            if building.is_accessible:
                accessible_buildings.append(building)

        # Check if both rooms are in accessible buildings
        start_building = None
        end_building = None
        for b in accessible_buildings:
            for floor in b.floors.values():
                if start_room_id in floor.rooms:
                    start_building = b
                if end_room_id in floor.rooms:
                    end_building = b

        if start_building and end_building:
            return {
                'is_accessible': True,
                'start': start_room_id,
                'end': end_room_id,
                'accessible_buildings': [b.name for b in accessible_buildings],
                'elevator_locations': self._get_elevator_locations(start_building, end_building),
                'ramp_locations': self._get_ramp_locations(),
                'guidance': self._generate_accessibility_guidance(start_building, end_building)
            }
        else:
            return {
                'is_accessible': False,
                'reason': 'One or both rooms are in non-accessible buildings',
                'alternatives': [b.name for b in accessible_buildings]
            }

    def _get_elevator_locations(self, start_building, end_building):
        """Get elevator locations for the route."""
        elevators = []
        for building in [start_building, end_building]:
            for floor in building.floors.values():
                for wp in floor.waypoints.values():
                    if wp.waypoint_type == 'elevator':
                        elevators.append({
                            'building': building.name,
                            'floor': floor.floor_number,
                            'waypoint_id': wp.id
                        })
        return elevators

    def _get_ramp_locations(self):
        """Get ramp locations across the campus."""
        ramps = []
        for building in self.campus.buildings.values():
            if building.is_accessible:
                ramps.append({
                    'building': building.name,
                    'location': 'Main Entrance',
                    'type': 'Wheelchair Ramp'
                })
        return ramps

    def _generate_accessibility_guidance(self, start_building, end_building):
        """Generate voice-friendly accessibility guidance."""
        guidance = []
        guidance.append(f"Starting from {start_building.name}.")

        if start_building.is_accessible:
            guidance.append("This building has elevator access to all floors.")
            for floor in start_building.floors.values():
                for wp in floor.waypoints.values():
                    if wp.waypoint_type == 'elevator':
                        guidance.append(f"Elevator available on Floor {floor.floor_number}.")
                        break

        if start_building != end_building:
            guidance.append(f"Proceed to {end_building.name} using the accessible pathway.")
            guidance.append("The path is wheelchair-friendly with no stairs.")

        guidance.append(f"Destination: {end_building.name}.")
        return "\n".join(guidance)

    def generate_voice_instructions(self, route_description):
        """Convert route description to voice-friendly instructions."""
        if not self.voice_guidance:
            return route_description

        # Simplify and make voice-friendly
        instructions = []
        for line in route_description.split('\n'):
            if line.strip():
                # Remove technical details, keep navigation info
                if any(kw in line for kw in ['stairs', 'elevator', 'floor', 'take', 'turn', 'proceed']):
                    instructions.append(line)

        return "\n".join(instructions)

    def check_building_accessibility(self, building_id):
        """Check if a building is fully accessible."""
        building = self.campus.get_building(building_id)
        if not building:
            return None

        has_elevator = False
        has_ramp = False
        for floor in building.floors.values():
            for wp in floor.waypoints.values():
                if wp.waypoint_type == 'elevator':
                    has_elevator = True

        return {
            'building': building.name,
            'is_accessible': building.is_accessible,
            'has_elevator': has_elevator,
            'has_ramp': has_ramp,
            'total_floors': len(building.floors)
        }


class NotificationService:
    """Provides real-time notifications for campus navigation."""

    def __init__(self):
        self.notifications = []
        self.subscribers = defaultdict(list)
        self.notification_history = []

    def send_notification(self, user_id, message, notification_type='info'):
        """Send a notification to a user."""
        notification = {
            'user_id': user_id,
            'message': message,
            'type': notification_type,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'read': False
        }
        self.notifications.append(notification)
        self.notification_history.append(notification)

        # Notify subscribers
        if user_id in self.subscribers:
            for callback in self.subscribers[user_id]:
                callback(notification)

        return notification

    def get_notifications(self, user_id):
        """Get all notifications for a user."""
        return [n for n in self.notifications if n['user_id'] == user_id]

    def get_unread_notifications(self, user_id):
        """Get unread notifications for a user."""
        return [n for n in self.notifications if n['user_id'] == user_id and not n['read']]

    def mark_as_read(self, notification_id):
        """Mark a notification as read."""
        for n in self.notifications:
            if n.get('id') == notification_id:
                n['read'] = True
                return True
        return False

    def subscribe(self, user_id, callback):
        """Subscribe a user to notifications."""
        self.subscribers[user_id].append(callback)

    def generate_sample_notifications(self):
        """Generate sample notifications for testing."""
        sample_notifications = [
            {'user_id': 'student_001', 'message': 'Room 101 has been relocated to Room 203', 'type': 'room_change'},
            {'user_id': 'student_001', 'message': 'You have arrived at Academic Block A', 'type': 'arrival'},
            {'user_id': 'student_001', 'message': 'Turn left at the corridor junction', 'type': 'direction'},
            {'user_id': 'student_001', 'message': 'Elevator available on Floor 2', 'type': 'accessibility'},
            {'user_id': 'student_002', 'message': 'Engineering Block is 200 meters away', 'type': 'distance'},
            {'user_id': 'student_002', 'message': 'Library reading room is on Floor 1', 'type': 'destination'},
        ]

        for notif in sample_notifications:
            self.send_notification(notif['user_id'], notif['message'], notif['type'])

        return self.notifications

    def get_notification_statistics(self):
        """Get statistics about notifications."""
        total = len(self.notifications)
        unread = sum(1 for n in self.notifications if not n['read'])
        types = defaultdict(int)
        for n in self.notifications:
            types[n['type']] += 1
        return {
            'total_notifications': total,
            'unread_notifications': unread,
            'notification_types': dict(types)
        }
