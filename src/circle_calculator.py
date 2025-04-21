import math

def calculate_circle_area(radius):
    """
    Calculate the area of a circle given its radius.
    
    Args:
        radius (float): The radius of the circle
        
    Returns:
        float: The area of the circle
    """
    return math.pi * radius ** 2

def calculate_circle_circumference(radius):
    """
    Calculate the circumference of a circle given its radius.
    
    Args:
        radius (float): The radius of the circle
        
    Returns:
        float: The circumference of the circle
    """
    return 2 * math.pi * radius 