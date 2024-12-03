import serial
import numpy as np
import io
import time
from flask import Flask, Response
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use 'Agg' backend to avoid window pop-up

# Serial Port Configuration
SERIAL_PORT = "COM3"  # Replace with the correct port for your system
BAUD_RATE = 115200
WIDTH = 32  # Width of the MLX90640 sensor grid
HEIGHT = 24  # Height of the MLX90640 sensor grid

# Initialize Flask app
app = Flask(__name__)

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

def generate_image():
    """
    Continuously fetches new data and generates a streaming image for Flask.
    """
    while True:
        try:
            temp_data = read_serial_data()
            temp_data = np.fliplr(temp_data)  # Flip the data horizontally to fix the mirroring

            # Create a figure and save it to a BytesIO buffer
            fig, ax = plt.subplots()
            image = ax.imshow(temp_data, cmap='inferno', interpolation='nearest')
            plt.colorbar(image, ax=ax)
            ax.set_title("MLX90640 Thermal Camera")

            # Adjust the color limits based on the current frame
            image.set_clim(vmin=temp_data.min(), vmax=temp_data.max())

            # Save the plot to a bytes buffer instead of displaying it
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig)

            # Yield the image as a response to the client
            yield (b'--frame\r\n'
                   b'Content-Type: image/png\r\n\r\n' + buf.read() + b'\r\n')

            # Wait for a short period before fetching the next frame
            time.sleep(0.2)  # 200ms delay (adjust as needed)
        except Exception as e:
            print(f"Error in generating image: {e}")
            continue

@app.route('/')
def index():
    """
    Returns the main page that will show the live video stream.
    """
    return '''<html>
                <body>
                    <h1>Thermal Camera Stream</h1>
                    <img src="/video_feed" width="640" height="480"/>
                </body>
              </html>'''

@app.route('/video_feed')
def video_feed():
    """
    Video streaming route. Returns the image stream for the thermal camera.
    """
    return Response(generate_image(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=8000, threaded=True)
    except KeyboardInterrupt:
        print("Server stopped.")
    finally:
        ser.close()  # Ensure the serial connection is closed when the server stops.
