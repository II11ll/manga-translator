from typing import List, Tuple

def merge_adjacent_regions(regions: List[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float], Tuple[float, float]]]) -> List[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float], Tuple[float, float]]]:
    """
    Merge adjacent regions based on their x-coordinates.
    
    Args:
    - regions (List[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float], Tuple[float, float]]]): List of regions defined by their four corner points.
    
    Returns:
    - List of merged regions.
    """
    # Sort regions based on the x-coordinate of their leftmost point
    regions.sort(key=lambda x: x[0][0])
    
    merged_regions = []
    current_region = regions[0]

    for next_region in regions[1:]:
        # Check if the right boundary of the current region is adjacent to the left boundary of the next region
        if current_region[1][0] == next_region[0][0] and current_region[1][1] == next_region[0][1] and current_region[2][1] == next_region[3][1]:
            # If they are adjacent, merge them
            current_region = (current_region[0], next_region[1], next_region[2], current_region[3])
        else:
            # If not adjacent, add the current region to the list and move to the next one
            merged_regions.append(current_region)
            current_region = next_region

    # Add the last region
    merged_regions.append(current_region)
    
    return merged_regions

# Example usage
regions = [
    ((1006.0, 1837.0), (1058.0, 1837.0), (1058.0, 1967.0), (1006.0, 1967.0)),
    ((1058.0, 1837.0), (1100.0, 1837.0), (1100.0, 1967.0), (1058.0, 1967.0)),
    # Add more regions as needed
]

merged_regions = merge_adjacent_regions(regions)
print(merged_regions)
