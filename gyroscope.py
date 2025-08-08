class GyroscopeSimulated:
    
    def __init__(self):
        self.angular_velocity = 0.0
        self.orientation = 0.0

    def update(self, angular_velocity, dt_ms):
        self.angular_velocity = angular_velocity
        self.orientation += angular_velocity * (dt_ms / 1000.0)

    def read_angular_velocity(self):
        return self.angular_velocity

    def read_orientation(self):
        return self.orientation
