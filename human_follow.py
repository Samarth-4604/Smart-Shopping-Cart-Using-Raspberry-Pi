#!/usr/bin/env python3
"""
human_follow.py

This script uses a Raspberry Pi camera and OpenCV’s MobileNetSSD model
to detect and follow a person. Movement commands are sent over serial
to an Arduino Uno‑based motor controller.

Commands sent to Arduino Uno:
  - 'F' → Move Forward
  - 'L' → Turn Left
  - 'R' → Turn Right
  - 'S' → Stop
"""

import cv2
import serial
import time
from picamera2 import Picamera2

# ─── 1. CONFIGURATION ─────────────────────────────────────────────────────────

# Serial port settings — change to your Arduino Uno device if needed
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE   = 9600
TIMEOUT     = 1  # seconds

# Path to the Caffe model files — put these in the same folder as this script
MODEL_PROTOTXT = 'deploy.prototxt'
MODEL_WEIGHTS  = 'MobileNetSSD_deploy.caffemodel'

# Detection settings
CONFIDENCE_THRESHOLD = 0.30  # only consider detections above this confidence
PERSON_CLASS_ID     = 15     # class 15 in MobileNetSSD = "person"

# Camera settings
CAMERA_RESOLUTION = (640, 480)

# ─── 2. INITIALIZATION ─────────────────────────────────────────────────────────

# 2.1 Setup serial connection to Arduino Uno
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
time.sleep(2)  # allow Arduino to reset

# 2.2 Load the MobileNetSSD neural network
net = cv2.dnn.readNetFromCaffe(MODEL_PROTOTXT, MODEL_WEIGHTS)

# 2.3 Initialize PiCamera2 for live video capture
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": CAMERA_RESOLUTION})
picam2.configure(config)
picam2.start()

# ─── 3. MAIN LOOP ──────────────────────────────────────────────────────────────

try:
    while True:
        # 3.1 Capture one frame from the camera
        frame = picam2.capture_array()
        
        # 3.2 Convert from BGRA (default) to BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        # 3.3 Show the live video window
        cv2.imshow("Camera Feed", frame)
        
        # 3.4 Prepare the frame for object detection
        blob = cv2.dnn.blobFromImage(
            image=frame,
            scalefactor=0.007843,
            size=(300, 300),
            mean=(127.5, 127.5, 127.5),
            swapRB=False
        )
        net.setInput(blob)
        detections = net.forward()
        
        # Default command is Stop
        command = 'S'
        person_detected = False
        
        # 3.5 Loop over all detections
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            class_id   = int(detections[0, 0, i, 1])
            
            # Only look for people with high enough confidence
            if confidence > CONFIDENCE_THRESHOLD and class_id == PERSON_CLASS_ID:
                # Compute the bounding box coordinates
                box = detections[0, 0, i, 3:7] * [
                    frame.shape[1],  # width
                    frame.shape[0],  # height
                    frame.shape[1],
                    frame.shape[0]
                ]
                (startX, startY, endX, endY) = box.astype("int")
                
                # Find the horizontal center of the person
                centerX = (startX + endX) // 2
                
                # Decide movement based on where the person is in the frame
                thirds = frame.shape[1] // 3
                if centerX < thirds:
                    command = 'L'  # person is on left → turn left
                elif centerX > 2 * thirds:
                    command = 'R'  # person is on right → turn right
                else:
                    command = 'F'  # person is centered → move forward
                
                person_detected = True
                break  # stop after first person found
        
        # 3.6 If no person was detected, stay or stop
        if not person_detected:
            command = 'S'
        
        # 3.7 Send the command to Arduino Uno
        ser.write(command.encode())
        
        # 3.8 (Optional) Read any debug response from Arduino Uno
        if ser.in_waiting > 0:
            try:
            response = ser.readline().decode().strip()
                print("Arduino Uno:", response)
            except UnicodeDecodeError:
                pass
        
        # 3.9 Small delay to control loop speed
        time.sleep(0.1)
        
        # 3.10 Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Stopped by user (Ctrl+C)")

finally:
    # ─── 4. CLEANUP ────────────────────────────────────────────────────────────
    ser.write(b'S')           # ensure motors are stopped
    time.sleep(0.1)
    picam2.stop()             # stop camera
    ser.close()               # close serial port
    cv2.destroyAllWindows()   # close any OpenCV windows
    print("Program ended. Motors stopped.")
