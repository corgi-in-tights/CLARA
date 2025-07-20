import serial
import time


class ArduinoEye:
    def __init__(self, port="/dev/tty.usbmodem11401", baud=115200):
        self.ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # allow Arduino to settle
        print("Serial connection established")

    def send(self, command: str):
        full_cmd = command.strip() + "\n"
        self.ser.write(full_cmd.encode("utf-8"))
        print(f">> Sent: {full_cmd.strip()}")

        # Optional: print Arduino's response
        time.sleep(0.05)
        while self.ser.in_waiting:
            response = self.ser.readline().decode("utf-8").strip()
            print(f"<< {response}")

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

eye.awake()
time.sleep(1)

eye.thinking()
time.sleep(1)

eye.talking()
time.sleep(1)

eye.asleep()
time.sleep(1)

eye.close()
