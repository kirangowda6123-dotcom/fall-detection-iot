import math

class FallDetector:
    def __init__(self, threshold=3.0):
        self.threshold = threshold

    def check_for_fall(self, x, y, z):
        g_force = math.sqrt(x**2 + y**2 + z**2)
        if g_force > self.threshold:
            return True, g_force
        return False, g_force