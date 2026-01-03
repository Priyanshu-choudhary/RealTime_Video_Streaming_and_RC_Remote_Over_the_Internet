#!/usr/bin/env python3
import serial
import time

class SerialSender:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, packet_delay=0.002):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.last_packet = None
        self.packet_delay = packet_delay  # small pause between packets

    def open_serial(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0
            )
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            # Wait for device to be fully ready
            time.sleep(1.0)

            # Send init packet
            init_packet = bytes([0xAA, 0x00, 0x00, 0x00])
            self.ser.write(init_packet)
            self.ser.flush()
            print(f"Sent init packet: {[hex(b) for b in init_packet]}")

            print(f"Serial port opened: {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            return False

    def close_serial(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port closed")

    def send_motor_command(self, direction, speed_L, speed_R):
        if not self.ser or not self.ser.is_open:
            return False

        direction = max(0, min(direction, 255))
        speed_L = max(0, min(speed_L, 255))
        speed_R = max(0, min(speed_R, 255))
        packet = bytes([0xAA, direction, speed_L, speed_R])

        # if packet == self.last_packet:
        #     return True  # avoid duplicate spam

        try:
            self.ser.write(packet)
            # time.sleep(100)
            self.ser.flush()
            self.last_packet = packet
            # print(f"Sent: {direction}, {speed_L}, {speed_R}")

            # small delay to let device process
            if self.packet_delay:
                time.sleep(self.packet_delay)

            return True
        except serial.SerialException as e:
            print(f"Error sending packet: {e}")
            return False

    def stop(self):
        return self.send_motor_command(0, 0, 0)
