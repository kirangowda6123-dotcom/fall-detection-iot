const socket = io();
const statusText = document.getElementById('status-text');
const accelVal = document.getElementById('accel-val');
const overlay = document.getElementById('emergency-overlay');
const gaugeBar = document.getElementById('gauge-bar');
const logBody = document.getElementById('log-body');

// 1. Function to show side messages
// --- REPLACE LINES 9 TO 28 WITH THIS ---
socket.on('update', (data) => {
    // We only update if the big red alert is NOT currently active
    const overlay = document.getElementById('emergency-overlay');
    const isAlerting = overlay && !overlay.classList.contains('hidden');

    if (!isAlerting) {
        // 1. Update the Big G-Force Number
        const accelVal = document.getElementById('accel-val');
        if (accelVal) accelVal.innerText = data.value;

        // 2. Update the visual Gauge Bar
        const gaugeBar = document.getElementById('gauge-bar');
        if (gaugeBar) {
            const percentage = Math.min((data.value / 4) * 100, 100);
            gaugeBar.style.width = percentage + "%";
        }

        // 3. Update the Current Status Text (Walking)
        const statusText = document.getElementById('status-text');
        if (statusText) {
            statusText.innerText = data.status || "Walking";
            statusText.style.color = (data.status === "Walking") ? "#2ecc71" : "#f39c12";
        }
    }
});

// 2. Alert Trigger Logic
function triggerEmergencyUI(force) {
    // 1. Show the simple status update on the dashboard
    const statusText = document.getElementById('status-text');
    statusText.innerText = "FALL DETECTED!";
    statusText.style.color = "#ff4d4d";
    
    // 2. Update the Big Number to the specific fall impact
    document.getElementById('accel-val').innerText = force;
    
    // 3. Update the Gauge to full
    const gaugeBar = document.getElementById('gauge-bar');
    if(gaugeBar) gaugeBar.style.width = "100%";

    // 4. SHOW THE SLIDE-IN MESSAGE (This is the fix)
    showInteractiveToast();

    // 5. Add entry to the Recent Activity Log table
    addLogEntry("FALL DETECTED", force);
}
// 3. Reset Button Function
function resetAlert() {
    const statusCard = document.querySelector('.status-card');
    const resetContainer = document.getElementById('reset-container');

    // Reset everything to normal
    statusCard.classList.remove('alert-active');
    resetContainer.classList.add('hidden');
    
    statusText.innerText = "Monitoring...";
    statusText.style.color = "#2ecc71";
    
    console.log("System Reset - Monitoring Resumed.");
}

// 4. Log Entry with Time Button
function addLogEntry(eventType, forceValue) {
    const now = new Date();
    const timeStr = now.toLocaleTimeString(); 
    const row = document.createElement('tr');
    row.innerHTML = `
        <td style="padding: 10px;">${timeStr}</td>
        <td>${eventType}</td>
        <td style="color:red; font-weight:bold;">${forceValue} G</td>
        <td><button onclick="alert('Time: ${timeStr}')" style="cursor:pointer; padding:5px; background:#3498db; color:white; border:none; border-radius:4px;">VIEW TIME</button></td>
    `;
    logBody.insertBefore(row, logBody.firstChild);
}

// 5. Automatic & Manual Listeners
socket.on('alert', (data) => { triggerEmergencyUI(data.value); });

document.getElementById('trigger-btn').addEventListener('click', () => {
    const force = (Math.random() * (6.0 - 3.5) + 3.5).toFixed(2);
    triggerEmergencyUI(force); 
});

function clearLogs() { logBody.innerHTML = ""; }

function showInteractiveToast() {
    console.log("Interactive Toast Triggered");
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = "position: fixed; top: 20px; right: 20px; z-index: 10000;";
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.style.cssText = "background: #333; color: white; padding: 15px 25px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #e74c3c; box-shadow: 0 4px 10px rgba(0,0,0,0.3); animation: slideIn 0.5s forwards;";
    
    const timerId = 'timer-' + Date.now();

    toast.innerHTML = `
        <div style="margin-bottom: 10px;">
            <strong>⚠️ Fall Detected!</strong><br>
            Are you hurt? Auto-call in <span id="${timerId}" style="color: #f39c12; font-weight: bold;">15</span>s
        </div>
        <div style="display: flex; gap: 10px;">
            <button onclick="handleResponse(this, 'fine')" style="background: #2ecc71; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">I'm Fine</button>
            <button onclick="handleResponse(this, 'help')" style="background: #e74c3c; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">Need Help</button>
        </div>
    `;
    
    container.appendChild(toast);

    let timeLeft = 15;
    const interval = setInterval(() => {
        timeLeft--;
        const span = document.getElementById(timerId);
        if(span) span.innerText = timeLeft;

        if (timeLeft <= 0) {
            clearInterval(interval);
            handleResponse({ parentNode: { parentNode: toast } }, 'help');
        }
    }, 1000);

    toast.dataset.timerId = interval;
}

window.handleResponse = function(btn, action) {
    const toast = btn.parentNode.parentNode;
    
    if (toast.dataset.timerId) clearInterval(toast.dataset.timerId);

    if (action === 'fine') {
        toast.remove();
        resetAlert();
        addLogEntry("User Confirmed: OK", "0.00");
    } else {
        toast.innerHTML = "<strong>🚨 Help Requested!</strong><br>Caretaker has been notified.";
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    }
};