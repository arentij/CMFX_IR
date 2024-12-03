# SERIAL_PORT = '/dev/cu.usbserial-0001'  # Replace with your serial port
import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Serial Port Configuration
SERIAL_PORT = '/dev/cu.usbserial-0001'  # Replace with the correct port for your system
BAUD_RATE = 115200
WIDTH = 32  # Width of the MLX90640 sensor grid
HEIGHT = 24  # Height of the MLX90640 sensor grid

# Initialize Serial Connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

def read_serial_data():
    """
    Reads a full frame of temperature data from the serial connection.
    Assumes the ESP32 sends data row by row, separated by newlines.
    """
    data = []
    while len(data) < WIDTH * HEIGHT:
        line = ser.readline().decode('utf-8').strip()
        if not line:
            continue
        try:
            # Split the line into individual temperatures
            values = [float(val) for val in line.split()]
            data.extend(values)
        except ValueError:
            # Skip invalid lines
            continue
    return np.array(data).reshape((HEIGHT, WIDTH))

# Initialize Plot
fig, ax = plt.subplots()
# fig=fig[][]
image = ax.imshow(np.zeros((HEIGHT, WIDTH)), cmap='inferno', interpolation='nearest')
plt.colorbar(image, ax=ax)
ax.set_title("MLX90640 Thermal Camera")

def update(frame):
    """
    Fetch new data from the ESP32 and update the image.
    """
    try:
        temp_data = read_serial_data()
        temp_data = np.fliplr(temp_data)
        image.set_data(temp_data)
        image.set_clim(vmin=temp_data.min(), vmax=temp_data.max())  # Adjust color scale
    except Exception as e:
        print(f"Error reading data: {e}")
    return [image]

# Use Matplotlib Animation for Live Updates
ani = FuncAnimation(fig, update, interval=200)  # Refresh every 200 ms

# Display the Plot
plt.show()

# Close the serial connection on exit
ser.close()
