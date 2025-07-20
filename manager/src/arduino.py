import serial
import time


class ArduinoEye:
    def __init__(self, port="/dev/tty.usbmodem11401", baud=115200):
        self.ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)
        print("Serial connection established")

    def send(self, command: str):
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
