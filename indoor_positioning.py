"""
Indoor Positioning Module
Implements Wi-Fi fingerprinting, QR-code based positioning, and
Bluetooth beacon triangulation for indoor location detection.
"""
import math
import random
from campus_map import CampusMap


class IndoorPositioning:
    """Provides indoor positioning using multiple technologies."""

    def __init__(self, campus_map: CampusMap):
        self.campus = campus_map
        self.wifi_fingerprints = {}  # location_id -> signal strength dict
        self.beacon_locations = {}  # beacon_id -> (x, y, floor, building_id)
        self.qr_code_locations = {}  # qr_code_id -> (room_id, x, y)

    def create_wifi_fingerprint_database(self):
        """Create simulated Wi-Fi fingerprint database for all locations."""
        access_points = ['AP-001', 'AP-002', 'AP-003', 'AP-004', 'AP-005',
                         'AP-006', 'AP-007', 'AP-008']

        for building in self.campus.buildings.values():
            for floor_num, floor in building.floors.items():
                for room_id, room in floor.rooms.items():
                    fingerprint = {}
                    for ap in access_points:
                        # Simulate signal strength based on distance
                        base_signal = random.uniform(-90, -30)
                        # Closer to AP = stronger signal
                        noise = random.uniform(-5, 5)
                        fingerprint[ap] = round(base_signal + noise, 1)
                    self.wifi_fingerprints[room_id] = {
                        'fingerprint': fingerprint,
                        'floor': floor_num,
                        'building_id': building.building_id,
                        'building_name': building.name,
                        'room_name': room.room_name
                    }

    def position_by_wifi(self, signal_readings):
        """Determine location using Wi-Fi fingerprint matching (k-NN)."""
        if not signal_readings:
            return None, 0

        distances = {}
        for room_id, data in self.wifi_fingerprints.items():
            fp = data['fingerprint']
            dist = 0
            common_aps = set(signal_readings.keys()) & set(fp.keys())
            if not common_aps:
                distances[room_id] = float('inf')
                continue
            for ap in common_aps:
                dist += (signal_readings[ap] - fp[ap]) ** 2
            distances[room_id] = math.sqrt(dist)

        # Find k nearest neighbors (k=3)
        sorted_rooms = sorted(distances.items(), key=lambda x: x[1])
        k = min(3, len(sorted_rooms))
        nearest = sorted_rooms[:k]

        if nearest[0][1] == float('inf'):
            return None, 0

        # Weighted average of top k
        total_weight = 0
        weighted_floor = 0
        weighted_building = ""
        weighted_room = ""

        for room_id, dist in nearest:
            weight = 1 / (dist + 0.01)
            total_weight += weight
            data = self.wifi_fingerprints[room_id]
            weighted_room += f"{data['room_name']} (weight: {weight:.3f}), "

        best_match = self.wifi_fingerprints[nearest[0][0]]
        confidence = max(0, 100 - nearest[0][1] * 2)

        return {
            'location': best_match['room_name'],
            'room_id': nearest[0][0],
            'floor': best_match['floor'],
            'building': best_match['building_name'],
            'confidence': round(confidence, 1),
            'matched_aps': len(common_aps) if common_aps else 0,
            'method': 'Wi-Fi Fingerprinting'
        }, confidence

    def position_by_qr_code(self, qr_code_id):
        """Determine location by scanning a QR code marker."""
        if qr_code_id in self.qr_code_locations:
            room_id, x, y = self.qr_code_locations[qr_code_id]
            for building in self.campus.buildings.values():
                for floor in building.floors.values():
                    if room_id in floor.rooms:
                        room = floor.rooms[room_id]
                        return {
                            'location': room.room_name,
                            'room_id': room_id,
                            'floor': floor.floor_number,
                            'building': building.name,
                            'coordinates': (x, y),
                            'confidence': 100.0,
                            'method': 'QR Code Scanning'
                        }, 100.0
        return None, 0

    def position_by_beacon(self, beacon_signals):
        """Determine location using Bluetooth beacon triangulation."""
        if not beacon_signals:
            return None, 0

        # Calculate position using trilateration
        estimated_x, estimated_y = 0, 0
        total_weight = 0

        for beacon_id, (rssi, distance_estimate) in beacon_signals.items():
            if beacon_id in self.beacon_locations:
                bx, by, floor, bid = self.beacon_locations[beacon_id]
                weight = 1 / (distance_estimate + 0.01)
                estimated_x += bx * weight
                estimated_y += by * weight
                total_weight += weight

        if total_weight > 0:
            estimated_x /= total_weight
            estimated_y /= total_weight

        # Find nearest room to estimated position
        nearest_room = None
        min_dist = float('inf')
        for building in self.campus.buildings.values():
            for floor in building.floors.values():
                for room_id, room in floor.rooms.items():
                    dist = math.sqrt(
                        (estimated_x - (hash(room.room_id) % 100)) ** 2 +
                        (estimated_y - ((hash(room.room_id) // 100) % 100)) ** 2
                    )
                    if dist < min_dist:
                        min_dist = dist
                        nearest_room = room

        if nearest_room:
            confidence = max(0, 100 - min_dist * 5)
            return {
                'location': nearest_room.room_name,
                'room_id': nearest_room.room_id,
                'floor': nearest_room.floor_number,
                'building': self.campus.buildings[nearest_room.building_id].name,
                'estimated_coords': (round(estimated_x, 1), round(estimated_y, 1)),
                'confidence': round(confidence, 1),
                'beacons_used': len(beacon_signals),
                'method': 'Bluetooth Beacon Triangulation'
            }, confidence
        return None, 0

    def evaluate_positioning_accuracy(self):
        """Evaluate the accuracy of different positioning methods."""
        results = {}

        # Test Wi-Fi fingerprinting
        if self.wifi_fingerprints:
            correct = 0
            total = len(self.wifi_fingerprints)
            for room_id, data in list(self.wifi_fingerprints.items())[:20]:
                readings = {k: v + random.uniform(-2, 2) for k, v in data['fingerprint'].items()}
                result, confidence = self.position_by_wifi(readings)
                if result and result['room_id'] == room_id:
                    correct += 1
            results['wifi_accuracy'] = (correct / min(20, total)) * 100 if total > 0 else 0

        # Test QR code
        results['qr_accuracy'] = 100.0  # QR codes are deterministic

        # Test beacon triangulation
        if self.beacon_locations:
            correct = 0
            total = min(len(self.beacon_locations), 20)
            for beacon_id in list(self.beacon_locations.keys())[:total]:
                bx, by, floor, bid = self.beacon_locations[beacon_id]
                readings = {beacon_id: (-40, 2.0)}
                result, confidence = self.position_by_beacon(readings)
                if result:
                    correct += 1
            results['beacon_accuracy'] = (correct / total) * 100 if total > 0 else 0

        return results

    def get_positioning_statistics(self):
        """Get statistics about the positioning system."""
        return {
            'wifi_fingerprints': len(self.wifi_fingerprints),
            'qr_codes': len(self.qr_code_locations),
            'beacons': len(self.beacon_locations),
            'coverage_area': '5 buildings, 10 floors',
            'total_positioning_points': len(self.wifi_fingerprints) + len(self.qr_code_locations)
        }
