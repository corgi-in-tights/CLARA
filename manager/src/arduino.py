import serial
import time


class ArduinoEye:
    def __init__(self, port="/dev/tty.usbmodem11401", baud=115200):
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            time.sleep(2)
            print("Serial connection established")
        except serial.SerialException as e:
            print(f"Error opening serial port {port}: {e}")
            self.ser = None
            print("Serial connection failed, ArduinoEye is not initialized.")

    def send(self, command: str):
        if self.ser is not None:
            full_cmd = command.strip() + "\n"
            self.ser.write(full_cmd.encode("utf-8"))
            print(f">> Arduino // Sent: {full_cmd.strip()}")

    def asleep(self):
        self.send("asleep")

    def awake(self):
        self.send("awake")

    def thinking(self):
        self.send("thinking")

    def talking(self):
        self.send("talking")

    def close(self):
        if self.ser.is_open:
            self.ser.close()
            print("Serial connection closed")

eye = ArduinoEye()
