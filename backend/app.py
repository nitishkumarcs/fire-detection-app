# app.py
from flask import Flask, request, jsonify
from db_config import init_db, db, FireAlert
from ultralytics import YOLO
import cv2
import numpy as np

app = Flask(__name__)

# Initialize DB
init_db(app)

# Load YOLO model
model = YOLO("fire.pt")


@app.route("/")
def home():
    return "🔥 Fire Detection Backend Running"


@app.route("/detect", methods=["POST"])
def detect_fire():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    filename = file.filename
    img = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)

    results = model(img)
    fire_detected = False
    confidence_val = 0.0

    for r in results[0].boxes:
        if int(r.cls[0]) == 0:  # fire class
            fire_detected = True
            confidence_val = float(r.conf[0])

    # Save to DB
    alert = FireAlert(
        detected=fire_detected,
        confidence=confidence_val,
        image_name=filename,
        location="Unknown"
    )
    db.session.add(alert)
    db.session.commit()

    return jsonify({
        "fire_detected": fire_detected,
        "confidence": confidence_val,
        "image_name": filename
    })


@app.route("/history", methods=["GET"])
def get_history():
    alerts = FireAlert.query.order_by(FireAlert.timestamp.desc()).all()
    history = []
    for a in alerts:
        history.append({
            "id": a.id,
            "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "location": a.location,
            "detected": a.detected,
            "confidence": a.confidence,
            "image_name": a.image_name
        })
    return jsonify(history)


@app.route("/history/clear", methods=["DELETE"])
def clear_history():
    db.session.query(FireAlert).delete()
    db.session.commit()
    return jsonify({"message": "All records deleted"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
