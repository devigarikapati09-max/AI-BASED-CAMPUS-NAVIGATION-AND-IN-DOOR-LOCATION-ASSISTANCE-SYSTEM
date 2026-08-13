"""
Analytics Service Module
Generates analytical charts for campus navigation system performance.
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from campus_map import CampusMap


def generate_building_distribution_chart(campus, output_path):
    """Generate chart showing building distribution and room counts."""
    buildings = list(campus.buildings.values())
    names = [b.name for b in buildings]
    room_counts = [len(b.get_all_rooms()) for b in buildings]
    floor_counts = [len(b.floors) for b in buildings]
    accessible = [b.is_accessible for b in buildings]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Room counts by building
    colors = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0']
    bars = ax1.bar(names, room_counts, color=colors[:len(names)], edgecolor='black', linewidth=0.5)
    ax1.set_title('Rooms per Building', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Building Name', fontsize=12)
    ax1.set_ylabel('Number of Rooms', fontsize=12)
    ax1.tick_params(axis='x', rotation=30)

    for bar, count in zip(bars, room_counts):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(count), ha='center', va='bottom', fontweight='bold', fontsize=11)

    # Floor distribution
    ax2.barh(names, floor_counts, color=colors[:len(names)], edgecolor='black', linewidth=0.5)
    ax2.set_title('Floors per Building', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Number of Floors', fontsize=12)
    ax2.set_ylabel('Building Name', fontsize=12)

    for i, count in enumerate(floor_counts):
        ax2.text(count + 0.1, i, str(count), va='center', fontweight='bold', fontsize=11)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def generate_room_type_distribution(campus, output_path):
    """Generate chart showing room type distribution across campus."""
    room_types = {}
    for building in campus.buildings.values():
        for room in building.get_all_rooms():
            if room.room_type in room_types:
                room_types[room.room_type] += 1
            else:
                room_types[room.room_type] = 1

    fig, ax = plt.subplots(figsize=(10, 6))
    types = list(room_types.keys())
    counts = list(room_types.values())
    colors = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0', '#00BCD4']

    wedges, texts, autotexts = ax.pie(
        counts, labels=types, autopct='%1.1f%%',
        colors=colors[:len(types)], startangle=90,
        textprops={'fontsize': 12}
    )
    for autotext in autotexts:
        autotext.set_fontweight('bold')
        autotext.set_fontsize(11)

    ax.set_title('Room Type Distribution Across Campus', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def generate_positioning_accuracy_chart(accuracy_data, output_path):
    """Generate chart comparing positioning accuracy of different methods."""
    methods = list(accuracy_data.keys())
    accuracies = [accuracy_data[m] for m in methods]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#4CAF50', '#2196F3', '#FF9800']
    bars = ax.bar(methods, accuracies, color=colors[:len(methods)], edgecolor='black', linewidth=0.5)

    ax.set_title('Indoor Positioning Accuracy Comparison', fontsize=14, fontweight='bold')
    ax.set_xlabel('Positioning Method', fontsize=12)
    ax.set_ylabel('Accuracy (%)', fontsize=12)
    ax.set_ylim(0, 110)

    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def generate_route_efficiency_chart(campus, output_path):
    """Generate chart showing route distances between buildings."""
    buildings = list(campus.buildings.values())
    n = len(buildings)
    distances = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            key = (buildings[i].building_id, buildings[j].building_id)
            if key in campus.inter_building_paths:
                distances[i][j] = campus.inter_building_paths[key]
            else:
                distances[i][j] = 0 if i == j else 999

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(distances, cmap='YlOrRd', aspect='auto')

    ax.set_xticks(range(n))
    ax.set_xticklabels([b.code for b in buildings], fontsize=10)
    ax.set_yticks(range(n))
    ax.set_yticklabels([b.code for b in buildings], fontsize=10)

    # Add text annotations
    for i in range(n):
        for j in range(n):
            if i != j and distances[i][j] < 999:
                ax.text(j, i, f'{distances[i][j]:.0f}m', ha='center', va='center',
                       fontsize=10, fontweight='bold')

    ax.set_title('Inter-Building Distances (meters)', fontsize=14, fontweight='bold')
    plt.colorbar(im, ax=ax, label='Distance (m)')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def generate_capacity_analysis_chart(campus, output_path):
    """Generate chart showing room capacity distribution."""
    capacities = []
    room_names = []
    for building in campus.buildings.values():
        for room in building.get_all_rooms():
            capacities.append(room.capacity)
            room_names.append(f"{room.room_number}\n({building.code})")

    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(capacities))
    colors = ['#2196F3' if c >= 50 else '#4CAF50' if c >= 30 else '#FF9800' for c in capacities]

    bars = ax.bar(x, capacities, color=colors, edgecolor='black', linewidth=0.3)
    ax.set_title('Room Capacity Distribution', fontsize=14, fontweight='bold')
    ax.set_xlabel('Room', fontsize=12)
    ax.set_ylabel('Capacity (students)', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(room_names, fontsize=8, rotation=45, ha='right')

    # Add horizontal line for average
    avg = np.mean(capacities)
    ax.axhline(y=avg, color='red', linestyle='--', linewidth=2, label=f'Average: {avg:.1f}')
    ax.legend(fontsize=11)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def generate_accessibility_map_chart(campus, output_path):
    """Generate chart showing accessibility status of campus buildings."""
    buildings = list(campus.buildings.values())
    names = [b.name for b in buildings]
    accessible = [1 if b.is_accessible else 0 for b in buildings]
    floors = [len(b.floors) for b in buildings]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(buildings))
    width = 0.35

    bars1 = ax.bar(x - width/2, floors, width, label='Floors', color='#2196F3', edgecolor='black')
    bars2 = ax.bar(x + width/2, accessible, width, label='Accessible (1=Yes, 0=No)', color='#4CAF50', edgecolor='black')

    ax.set_title('Campus Accessibility Overview', fontsize=14, fontweight='bold')
    ax.set_xlabel('Building', fontsize=12)
    ax.set_ylabel('Count / Status', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10, rotation=30)
    ax.legend(fontsize=11)
    ax.set_ylim(0, max(max(floors), 2))

    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height}', ha='center', va='bottom', fontweight='bold', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def generate_notification_stats_chart(notification_stats, output_path):
    """Generate chart showing notification type distribution."""
    types = list(notification_stats['notification_types'].keys())
    counts = list(notification_stats['notification_types'].values())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Bar chart
    colors = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0']
    bars = ax1.bar(types, counts, color=colors[:len(types)], edgecolor='black', linewidth=0.5)
    ax1.set_title('Notification Types', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Type', fontsize=12)
    ax1.set_ylabel('Count', fontsize=12)
    ax1.tick_params(axis='x', rotation=30)

    for bar, count in zip(bars, counts):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                str(count), ha='center', va='bottom', fontweight='bold')

    # Pie chart
    ax2.pie(counts, labels=types, autopct='%1.1f%%',
            colors=colors[:len(types)], startangle=90,
            textprops={'fontsize': 10})
    ax2.set_title('Notification Distribution', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def generate_all_charts(campus, accuracy_data, notification_stats, output_dir='reports'):
    """Generate all analytical charts."""
    os.makedirs(output_dir, exist_ok=True)

    charts = {
        'building_distribution': f'{output_dir}/building_distribution.png',
        'room_type_distribution': f'{output_dir}/room_type_distribution.png',
        'positioning_accuracy': f'{output_dir}/positioning_accuracy.png',
        'route_efficiency': f'{output_dir}/route_efficiency.png',
        'capacity_analysis': f'{output_dir}/capacity_analysis.png',
        'accessibility_map': f'{output_dir}/accessibility_map.png',
        'notification_stats': f'{output_dir}/notification_stats.png',
    }

    generate_building_distribution_chart(campus, charts['building_distribution'])
    generate_room_type_distribution(campus, charts['room_type_distribution'])
    generate_positioning_accuracy_chart(accuracy_data, charts['positioning_accuracy'])
    generate_route_efficiency_chart(campus, charts['route_efficiency'])
    generate_capacity_analysis_chart(campus, charts['capacity_analysis'])
    generate_accessibility_map_chart(campus, charts['accessibility_map'])
    generate_notification_stats_chart(notification_stats, charts['notification_stats'])

    return charts
