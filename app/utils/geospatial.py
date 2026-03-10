"""
Geospatial Utility Functions

Provides geospatial calculations for proximity-based queries.

Key Functions:
- haversine_distance: Calculate distance between two lat/long coordinates
- find_projects_within_radius: Find all projects within a specified radius of a reference point
"""

import math
from typing import List, Dict, Tuple, Optional


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth using the Haversine formula.

    Args:
        lat1: Latitude of first point (degrees)
        lon1: Longitude of first point (degrees)
        lat2: Latitude of second point (degrees)
        lon2: Longitude of second point (degrees)

    Returns:
        Distance in kilometers

    Formula:
        a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
        c = 2 * atan2(√a, √(1−a))
        d = R * c

    where R = Earth's radius = 6371 km
    """
    # Earth's radius in kilometers
    R = 6371.0

    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance
    distance_km = R * c

    return distance_km


def find_projects_within_radius(
    reference_lat: float,
    reference_lon: float,
    all_projects: List[Dict],
    radius_km: float
) -> List[Dict]:
    """
    Find all projects within a specified radius of a reference point.

    Args:
        reference_lat: Latitude of reference point (degrees)
        reference_lon: Longitude of reference point (degrees)
        all_projects: List of project dictionaries with 'latitude' and 'longitude' fields
        radius_km: Maximum distance from reference point (kilometers)

    Returns:
        List of projects within radius, sorted by distance (closest first).
        Each project dict is augmented with 'distance_km' field.

    Example:
        >>> projects = [
        ...     {'projectName': {'value': 'Project A'}, 'latitude': {'value': 18.75}, 'longitude': {'value': 73.83}},
        ...     {'projectName': {'value': 'Project B'}, 'latitude': {'value': 18.76}, 'longitude': {'value': 73.84}}
        ... ]
        >>> nearby = find_projects_within_radius(18.755, 73.836, projects, 2.0)
    """
    projects_with_distance = []

    for project in all_projects:
        # Extract latitude/longitude (handle nested dict structure)
        lat_obj = project.get('latitude', {})
        lon_obj = project.get('longitude', {})

        lat = lat_obj.get('value') if isinstance(lat_obj, dict) else lat_obj
        lon = lon_obj.get('value') if isinstance(lon_obj, dict) else lon_obj

        # Skip projects without coordinates
        if lat is None or lon is None:
            continue

        # Calculate distance
        distance_km = haversine_distance(reference_lat, reference_lon, lat, lon)

        # Filter by radius (exclude the reference project itself with distance ~ 0)
        if distance_km > 0.01 and distance_km <= radius_km:
            # Add distance to project data
            project_with_dist = project.copy()
            project_with_dist['distance_km'] = distance_km
            projects_with_distance.append(project_with_dist)

    # Sort by distance (closest first)
    projects_with_distance.sort(key=lambda p: p['distance_km'])

    return projects_with_distance


def get_project_coordinates(project_name: str, all_projects: List[Dict]) -> Optional[Tuple[float, float]]:
    """
    Get the latitude and longitude of a project by name.

    Args:
        project_name: Name of the project to find
        all_projects: List of all project dictionaries

    Returns:
        Tuple of (latitude, longitude) if found, None otherwise

    Example:
        >>> projects = [{'projectName': {'value': 'Sara City'}, 'latitude': {'value': 18.755}, 'longitude': {'value': 73.836}}]
        >>> coords = get_project_coordinates('Sara City', projects)
        >>> coords
        (18.755, 73.836)
    """
    from app.utils.fuzzy_matcher import FuzzyMatcher

    project_name_normalized = FuzzyMatcher.normalize(project_name)

    for project in all_projects:
        proj_name_obj = project.get('projectName', {})
        proj_name = proj_name_obj.get('value', '') if isinstance(proj_name_obj, dict) else str(proj_name_obj)

        # Normalize project name for comparison (handles newlines, etc.)
        proj_name_normalized = FuzzyMatcher.normalize(proj_name)

        if proj_name_normalized == project_name_normalized:
            # Extract coordinates
            lat_obj = project.get('latitude', {})
            lon_obj = project.get('longitude', {})

            lat = lat_obj.get('value') if isinstance(lat_obj, dict) else lat_obj
            lon = lon_obj.get('value') if isinstance(lon_obj, dict) else lon_obj

            if lat is not None and lon is not None:
                return (lat, lon)

    return None


def get_distance_between_projects(
    source_project: str,
    target_project: str,
    all_projects: List[Dict]
) -> Optional[float]:
    """
    Calculate the Haversine distance between two projects using their coordinates.

    Args:
        source_project: Name of the source/reference project
        target_project: Name of the target project
        all_projects: List of all project dictionaries with latitude/longitude data

    Returns:
        Distance in kilometers if both projects found with valid coordinates, None otherwise

    Example:
        >>> projects = [
        ...     {'projectName': {'value': 'Sara City'}, 'latitude': {'value': 18.755}, 'longitude': {'value': 73.836}},
        ...     {'projectName': {'value': 'Gulmohar City'}, 'latitude': {'value': 18.752}, 'longitude': {'value': 73.830}}
        ... ]
        >>> distance = get_distance_between_projects('Sara City', 'Gulmohar City', projects)
        >>> distance  # Returns distance in km
        0.68
    """
    # Get coordinates for source project
    source_coords = get_project_coordinates(source_project, all_projects)
    if source_coords is None:
        return None

    # Get coordinates for target project
    target_coords = get_project_coordinates(target_project, all_projects)
    if target_coords is None:
        return None

    # Calculate Haversine distance
    source_lat, source_lon = source_coords
    target_lat, target_lon = target_coords

    distance_km = haversine_distance(source_lat, source_lon, target_lat, target_lon)

    return distance_km
