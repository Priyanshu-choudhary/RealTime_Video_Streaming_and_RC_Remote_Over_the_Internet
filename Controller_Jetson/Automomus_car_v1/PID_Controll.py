import time

class PID:
    def __init__(self, kp, ki, kd, setpoint=0, output_limits=(-100, 100)):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.setpoint = setpoint
        self._limits = output_limits
        self._prev_error = 0
        self._integral = 0
        self._last_time = time.time()

    def set_tunings(self, kp, ki, kd):
        """Changes the PID constants on the fly."""
        self.kp = kp
        self.ki = ki
        self.kd = kd
        # Optional: Some developers prefer to reset the integral when 
        # constants change to avoid sudden spikes in output.
        self.reset()
        # print(f"UPDATED..{kp} {ki} {kd}")


    def compute(self, measurement):
        now = time.time()
        dt = now - self._last_time
        
        # Prevent division by zero or huge jumps if timing is inconsistent
        if dt <= 0 or dt > 0.5: 
            self._last_time = now
            return 0
        
        error = self.setpoint - measurement
        
        # Proportional term
        p_term = self.kp * error
        
        # Integral term with Anti-Windup
        # We limit the integral so it can't exceed the total output limits
        self._integral += error * dt
        i_term = self.ki * self._integral
        
        # Clamp I-term to prevent windup
        lower, upper = self._limits
        i_term = max(lower, min(upper, i_term))
        
        # Derivative term (with simple low-pass filtering logic or guard)
        derivative = (error - self._prev_error) / dt
        d_term = self.kd * derivative
        
        output = p_term + i_term + d_term
        
        # Clamp total output
        output = max(lower, min(upper, output))
        
        self._prev_error = error
        self._last_time = now
        # print(output)
        return output

    def reset(self):
        """Call this when switching modes to clear old errors"""
        self._integral = 0
        self._prev_error = 0
        self._last_time = time.time()