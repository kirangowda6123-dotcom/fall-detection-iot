import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, redirect, url_for, request
from flask_socketio import SocketIO
import random 
import time
from datetime import datetime

# Essential: Importing your sensor logic
from sensor_module import FallDetector

app = Flask(__name__)
app.secret_key = 'fall_detection_secret_key' # Required for session management
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize detector with a 3.0G threshold
detector = FallDetector(threshold=3.0)

# In-memory storage for fall history
fall_history = [
    {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "status": "System Started",
        "value": 0.0
    }
]

# --- ROUTES FOR MULTIPLE PAGES ---

@app.route('/')
def root():
    """Redirect root URL to Login Page"""
    return redirect(url_for('login'))

@app.route('/dashboard')
def index():
    """Main Dashboard Page"""
    return render_template('index.html')

@app.route('/profile')
def profile():
    """Patient Profile Page"""
    return render_template('profile.html')

@app.route('/history')
def history():
    """Fall Analytics Page"""
    return render_template('history.html', history=fall_history)

@app.route('/settings')
def settings():
    """System Configuration Page"""
    return render_template('settings.html', threshold=detector.threshold)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    """Update system configuration"""
    try:
        new_threshold = float(request.form.get('threshold'))
        detector.threshold = new_threshold
        print(f"[SYSTEM] Threshold updated to: {detector.threshold} G")
    except (ValueError, TypeError):
        print("[ERROR] Invalid threshold value")
    return redirect(url_for('settings'))

@app.route('/logout')
def logout():
    """Logout and return to login page"""
    return redirect(url_for('login'))

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear all fall history records"""
    fall_history.clear()
    return redirect(url_for('history'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login Page"""
    if request.method == 'POST':
        # Add your actual authentication logic here
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration Page"""
    if request.method == 'POST':
        # Add your actual registration logic here
        return redirect(url_for('login'))
    return render_template('register.html')

# --- NOTIFICATION SYSTEM ---

def send_emergency_alert(impact_value):
    """
    Simulates sending an SMS or Call to the caretaker.
    For Raspberry Pi + IoT, integrate Twilio or GSM module here.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[EMERGENCY] Fall Detected! Impact: {impact_value}G")
    print(f"[SYSTEM] Calling Caretaker... Sending SMS with location and time: {timestamp}\n")
    # Example: twilio_client.messages.create(body=f"Fall Detected! {impact_value}G", ...)

# --- SENSOR SIMULATION LOGIC ---

def monitor_sensor():
    """Background task simulating accelerometer data"""
    print("Background Task: Sensor monitoring started...")
    # Set the first random fall to occur in 10-15 seconds
    next_fall_time = time.time() + random.uniform(20, 60)
    
    # Activity simulation state
    activity_state = "Walking"
    next_activity_change = time.time() + random.uniform(10, 20)
    
    while True:
        try:
            current_time = time.time()
            
            # Toggle between Walking and Sitting periodically
            if current_time >= next_activity_change:
                activity_state = "Sitting" if activity_state == "Walking" else "Walking"
                next_activity_change = current_time + random.uniform(10, 20)
            
            # Decide if we spike the value for a fall
            # NOTE: On Raspberry Pi, replace this block with real sensor reading (e.g., mpu6050)
            if current_time >= next_fall_time:
                # Simulated high impact force
                x, y, z = random.uniform(3.0, 5.0), random.uniform(3.0, 5.0), random.uniform(3.0, 5.0)
                # Reset timer for the next random fall event
                next_fall_time = time.time() + random.uniform(20, 60)
            else:
                if activity_state == "Sitting":
                    # Sitting: Low movement, stable near 1G
                    x, y, z = random.uniform(0.98, 1.02), random.uniform(0.0, 0.1), random.uniform(0.0, 0.1)
                else:
                    # Walking: Moderate movement
                    x, y, z = random.uniform(0.95, 1.15), random.uniform(0.95, 1.15), random.uniform(0.95, 1.15)
            
            is_fall, val = detector.check_for_fall(x, y, z)
            
            # Prepare data for the frontend
            status = "FALL DETECTED!" if is_fall else activity_state
            data = {
                "status": status, 
                "value": round(val, 2)
            }
            
            if is_fall:
                # Record the event in history
                timestamp = datetime.now()
                fall_history.insert(0, {
                    "date": timestamp.strftime("%Y-%m-%d"),
                    "time": timestamp.strftime("%H:%M:%S"),
                    "status": "FALL DETECTED",
                    "value": round(val, 2)
                })
                # Trigger the red alert UI
                socketio.emit('alert', data)
                # Send external notification (SMS/Call)
                send_emergency_alert(round(val, 2))
            
            # Always send the live data to keep the G-force moving
            socketio.emit('update', data)
            socketio.sleep(0.5)
        except Exception as e:
            print(f"Error in background task: {e}")
            socketio.sleep(1)

if __name__ == '__main__':
    # Start the background monitoring thread
    socketio.start_background_task(monitor_sensor)
    # Run the server on localhost:5000
    socketio.run(app, debug=True)