import config

class RCMixer:
    # Assuming RCMixer class constants are defined
    RC_MIN = config.RC_MIN
    RC_MAX = config.RC_MAX
    RC_CENTER = config.RC_CENTER
    RC_DEADBAND = config.RC_DEADBAND
    MAX_PWM_OUTPUT = config.MAX_PWM_OUTPUT
    MAX_CORRECTION_PWM  = config.MAX_CORRECTION_PWM 

    @staticmethod
    #If value is below min_val, it returns min_val , If value is above max_val, it returns max_val , other wise unchanged
    def clamp(value, min_val, max_val):
        return max(min_val, min(max_val, value))

    @staticmethod
    def rc_to_signed_255(rc_value):
        # A placeholder function for converting 1000-2000 to -255 to 255
        return RCMixer.clamp((rc_value - RCMixer.RC_CENTER) * 255 // (RCMixer.RC_CENTER - RCMixer.RC_MIN), -255, 255)

    @staticmethod
    def compute_motor_commands(throttle_rc, roll_rc, rc_reft_right_mixer_for_Forward):
        """
        Return (direction, pwm_motor1, pwm_motor2)
        direction: 1 forward, 2 reverse, 0 stop, 3 pivot right, 4 pivot left
        """
        # --- 1. Clamp and Prep Inputs ---
        throttle_rc = RCMixer.clamp(int(throttle_rc), RCMixer.RC_MIN, RCMixer.RC_MAX)
        roll_rc = RCMixer.clamp(int(roll_rc), RCMixer.RC_MIN, RCMixer.RC_MAX)
        rc_reft_right_mixer_for_Forward = RCMixer.clamp(int(rc_reft_right_mixer_for_Forward), RCMixer.RC_MIN, RCMixer.RC_MAX)

        thr_delta = throttle_rc - RCMixer.RC_CENTER
        roll_delta = roll_rc - RCMixer.RC_CENTER
        rc_mixer_Forward_delta = rc_reft_right_mixer_for_Forward - RCMixer.RC_CENTER





        # --- 2. Apply Deadband and Convert to Signed PWM (-255 to 255) ---
        if abs(thr_delta) <= RCMixer.RC_DEADBAND:
            th_signed = 0
        else:
            th_signed = RCMixer.rc_to_signed_255(throttle_rc)

        if abs(roll_delta) <= RCMixer.RC_DEADBAND:
            roll_signed = 0
        else:
            roll_signed = RCMixer.rc_to_signed_255(roll_rc)
        




        # --- 3. Calculate the Mixer Bias (Motor Correction) ---
        
        # Convert 1000-2000 to a signed adjustment from -RCMixer.MAX_CORRECTION_PWM  to +RCMixer.MAX_CORRECTION_PWM 
        
        #InShot map( 1000 , 2000) to (-30 , +30)
        correction_bias = RCMixer.clamp(
            rc_mixer_Forward_delta * RCMixer.MAX_CORRECTION_PWM  // (RCMixer.RC_CENTER - RCMixer.RC_MIN), 
            -RCMixer.MAX_CORRECTION_PWM , 
            RCMixer.MAX_CORRECTION_PWM 
        )
        


        # --- 4. Stop Logic ---
        if th_signed == 0 and roll_signed == 0:
            return 0, 0, 0

        # --- 5. Pure Pivot  (Throttle zero, Roll active) that means only roll is using and no throttle
        if th_signed == 0 and roll_signed != 0:
            pwm = RCMixer.clamp(abs(roll_signed), 0, RCMixer.MAX_PWM_OUTPUT)
            if roll_signed > 0:
                return 3, pwm, pwm  # Pivot Right
            else:
                return 4, pwm, pwm  # Pivot Left


        # --- 6. Initial Mixing  (Throttle + Roll) && (Throttle + Roll) ---
        left_signal = RCMixer.clamp(  (th_signed + roll_signed)  , -255, 255)
        right_signal = RCMixer.clamp(  (th_signed - roll_signed)  , -255, 255)

       
        # print(f"{left_signal} {right_signal}")
        # --- 7. Forward/Reverse Logic and CORRECTION APPLICATION ---
        
        # We only apply the trim if the robot is not actively turning with the roll stick.
        # This keeps the correction for straight-line driving only.
        # if abs(roll_signed) < RCMixer.RC_DEADBAND:
        #     # Correction: 
        #     # Positive bias (Aux > 1500) -> Add to Left, Subtract from Right
        #     # Negative bias (Aux < 1500) -> Subtract from Left, Add to Right
        #     left_signal += correction_bias
        #     right_signal -= correction_bias

        #     # Re-clamp the signals after correction to ensure they don't exceed MAX_PWM_OUTPUT
        #     left_signal = RCMixer.clamp(left_signal, -255, 255)
        #     right_signal = RCMixer.clamp(right_signal, -255, 255)


        if th_signed > 0:
            # Forward
            pwm_l = RCMixer.clamp(max(0, left_signal), 0, RCMixer.MAX_PWM_OUTPUT)
            pwm_r = RCMixer.clamp(max(0, right_signal), 0, RCMixer.MAX_PWM_OUTPUT)
            return 1, int(pwm_l), int(pwm_r)
        
        else: # th_signed < 0 (Reverse)
          
            
            pwm_l = RCMixer.clamp(max(0, -left_signal), 0, RCMixer.MAX_PWM_OUTPUT)
            pwm_r = RCMixer.clamp(max(0, -right_signal), 0, RCMixer.MAX_PWM_OUTPUT)
            return 2, int(pwm_l), int(pwm_r)
