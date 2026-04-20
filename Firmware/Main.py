import time
import threading
from flask import Flask, render_template, request, jsonify
from gpiozero import Robot, DistanceSensor
from luma.oled.device import ssd1306
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from PIL import ImageFont

# --- 1. Hardware Configuration ---
# TB6612FNG Motors: Left(PWM, Dir1, Dir2), Right(PWM, Dir1, Dir2)
robot = Robot(left=(12, 17, 27), right=(13, 22, 23))
ultrasonic = DistanceSensor(echo=21, trigger=20)

# OLED Setup
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

# --- 2. Global State ---
app = Flask(__name__)
ai_nav_active = False
current_status = "Idle"

# --- 3. OLED Display Logic ---
def update_oled():
    while True:
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            draw.text((5, 5), "A.U.R.O.R.A.", fill="white")
            draw.text((5, 25), f"Status: {current_status}", fill="white")
            draw.text((5, 45), f"Dist: {ultrasonic.distance*100:.1f}cm", fill="white")
        time.sleep(0.5)

# --- 4. AI Navigation Logic ---
def ai_navigation_loop():
    global ai_nav_active, current_status
    while True:
        if ai_nav_active:
            current_status = "AI Nav: ON"
            if ultrasonic.distance < 0.3:  # 30cm
                robot.stop()
                current_status = "Obstacle!"
                time.sleep(0.5)
                robot.right(0.5) # Basic avoidance
                time.sleep(1)
            else:
                robot.forward(0.4)
        time.sleep(0.1)

# --- 5. Flask Web Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

@app.route('/control', methods=['POST'])
def control():
    global ai_nav_active, current_status
    cmd = request.json.get('command')
    
    if cmd == 'forward': robot.forward(0.6)
    elif cmd == 'backward': robot.backward(0.6)
    elif cmd == 'left': robot.left(0.5)
    elif cmd == 'right': robot.right(0.5)
    elif cmd == 'stop': 
        robot.stop()
        ai_nav_active = False
    elif cmd == 'ai_on': ai_nav_active = True
    elif cmd == 'ai_off': ai_nav_active = False
    
    return jsonify(success=True)

if __name__ == '__main__':
    # Start background threads
    threading.Thread(target=update_oled, daemon=True).start()
    threading.Thread(target=ai_navigation_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
