import json
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import queue
import scipy.spatial.transform as transform

# --- Configuration ---
MQTT_BROKER = "localhost"
MQTT_TOPIC = "aruco"

# Initialize Plot
plt.ion()  # Turn on interactive mode
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

data_queue = queue.Queue()

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    markers = data.get("markers", {})

    data_queue.put(markers)

def draw_markers(markers):
    try:
        # Clear and update plot
        ax.cla()
        quivers_xyz = ([], [], [])
        quivers_uvw = (([], [], []), ([], [], []), ([], [], []))

        for m_id, content in markers.items():
            pos = content.get("position")
            rot = content.get("rotation")
            
            if content.get("origin"):
                ax.scatter(*pos, c='red', marker='o')

            for i in range(3):
                quivers_xyz[i].append(pos[i])

            ax.text(*pos, m_id, size=8)
            
            rot_matrix = transform.Rotation.from_rotvec(rot).as_matrix()

            for i in range(3):
                for j in range(3):
                    quivers_uvw[i][j].append(rot_matrix[:, i][j])


        axis_length = 0.04
        linewidth = 1

        for i, color in enumerate(('blue', 'green', 'red')):
            ax.quiver(*quivers_xyz, *(quivers_uvw[i]),
                            length=axis_length, color=color, linewidth=linewidth)


        # Set labels and fixed limits (adjust based on your scale)
        ax.set_xlabel('X Axis')
        ax.set_ylabel('Y Axis')
        ax.set_zlabel('Z Axis')
        ax.set_title("Real-time MQTT Marker Positions")

        bound = 0.15
        ax.set_ybound(-bound, bound)
        ax.set_xbound(-bound, bound)
        ax.set_zbound(-bound, bound)
        
        plt.draw()
        plt.pause(0.01)

    except Exception as e:
        raise
        print(f"Error parsing data: {e}")

# --- MQTT Setup ---
client = mqtt.Client()
client.on_message = on_message

print(f"Connecting to {MQTT_BROKER}...")
client.connect(MQTT_BROKER, 1883, 60)
client.subscribe(MQTT_TOPIC)

print("Listening for data... Press Ctrl+C to stop.")
client.loop_start()

try:
    while True:
        marker = data_queue.get()
        draw_markers(marker)
except KeyboardInterrupt:
    client.loop_stop()
    print("Stopped.")