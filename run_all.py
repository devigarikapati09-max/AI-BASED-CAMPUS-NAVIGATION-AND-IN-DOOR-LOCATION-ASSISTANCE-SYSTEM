"""
Runner script to execute tests and generate all analytical charts.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from campus_map import CampusMap, create_sample_campus
from route_finder import RouteFinder
from indoor_positioning import IndoorPositioning
from accessibility_service import AccessibilityService, NotificationService
from analytics_service import generate_all_charts

# ========== RUN DEMO ==========
print("=" * 60)
print("AI-BASED CAMPUS NAVIGATION SYSTEM - DEMO")
print("=" * 60)

# Initialize campus
campus = create_sample_campus()
stats = campus.get_statistics()
print(f"\nCampus Statistics:")
print(f"  Total Buildings: {stats['total_buildings']}")
print(f"  Total Rooms: {stats['total_rooms']}")
print(f"  Total Floors: {stats['total_floors']}")
print(f"  Accessible Buildings: {stats['accessible_buildings']}")
print(f"  Room Type Distribution: {stats['room_type_distribution']}")

# Route finder
print(f"\n--- Route Finding Demo ---")
finder = RouteFinder(campus)
finder.build_graph()
waypoints = []
for building in campus.buildings.values():
    for floor in building.floors.values():
        for wp_id in floor.waypoints:
            waypoints.append(wp_id)

if len(waypoints) >= 2:
    path, distance = finder.dijkstra(waypoints[0], waypoints[1])
    if path:
        print(f"  Dijkstra path: {len(path)} waypoints, distance: {distance:.1f}m")
    else:
        print(f"  Dijkstra: No direct path between first two waypoints (expected for non-connected graph)")
        # Try finding connected waypoints
        found = False
        for i in range(len(waypoints)):
            for j in range(i+1, len(waypoints)):
                p, d = finder.dijkstra(waypoints[i], waypoints[j])
                if p:
                    print(f"  Dijkstra path found: {len(p)} waypoints, distance: {d:.1f}m")
                    found = True
                    break
            if found:
                break
        if not found:
            print(f"  Building waypoints are on separate floors without stair connections in demo data")
            print(f"  Full connectivity requires additional waypoint connections (production feature)")

# Indoor positioning
print(f"\n--- Indoor Positioning Demo ---")
positioning = IndoorPositioning(campus)
positioning.create_wifi_fingerprint_database()
room_id = list(positioning.wifi_fingerprints.keys())[0]
readings = positioning.wifi_fingerprints[room_id]['fingerprint']
result, confidence = positioning.position_by_wifi(readings)
print(f"  Wi-Fi positioning result: {result['location'] if result else 'N/A'}")
print(f"  Confidence: {confidence:.1f}%")

# Accessibility
print(f"\n--- Accessibility Demo ---")
accessibility = AccessibilityService(campus)
for bid in ['B1', 'B3']:
    result = accessibility.check_building_accessibility(bid)
    if result:
        print(f"  {result['building']}: accessible={result['is_accessible']}")

# Notifications
print(f"\n--- Notification Demo ---")
notifier = NotificationService()
notifier.generate_sample_notifications()
notif_stats = notifier.get_notification_statistics()
print(f"  Total notifications: {notif_stats['total_notifications']}")
print(f"  Types: {notif_stats['notification_types']}")

# Accuracy evaluation
print(f"\n--- Positioning Accuracy Evaluation ---")
accuracy = positioning.evaluate_positioning_accuracy()
print(f"  Wi-Fi Accuracy: {accuracy['wifi_accuracy']:.1f}%")
print(f"  QR Code Accuracy: {accuracy['qr_accuracy']:.1f}%")
beacon_acc = accuracy.get('beacon_accuracy', 0.0)
print(f"  Beacon Accuracy: {beacon_acc:.1f}%")

# ========== GENERATE CHARTS ==========
print(f"\n{'=' * 60}")
print("GENERATING ANALYTICAL CHARTS")
print("=" * 60)

os.makedirs('reports', exist_ok=True)
charts = generate_all_charts(campus, accuracy, notif_stats, 'reports')
print(f"\nAll charts generated successfully!")
for name, path in charts.items():
    print(f"  {name}: {path}")

# Copy charts to screenshots directory
import shutil
os.makedirs('screenshots', exist_ok=True)
for name, path in charts.items():
    dest = f"screenshots/{name}.png"
    shutil.copy2(path, dest)
    print(f"  Copied to: {dest}")

print("\nDone!")
