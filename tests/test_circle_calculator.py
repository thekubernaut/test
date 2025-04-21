import pytest
from src.circle_calculator import calculate_circle_area

def test_calculate_circle_area():
    # Test with radius 1
    assert calculate_circle_area(1) == pytest.approx(3.14159, rel=1e-5)
    
    # Test with radius 5
    assert calculate_circle_area(5) == pytest.approx(78.5398, rel=1e-5)
    
    # Test with radius 0
    assert calculate_circle_area(0) == 0 