from flask import Flask, request, jsonify, render_template
import easyocr
import cv2
import numpy as np
from PIL import Image, ImageChops
import os

app = Flask(__name__)
reader = easyocr.Reader(['en'])

def perform_ela(img_path):
    """Detects digital tampering using Error Level Analysis."""
    original_path = img_path
    temp_path = "temp_resave.jpg"
    
    # Save image at 90% quality
    im = Image.open(original_path).convert('RGB')
    im.save(temp_path, 'JPEG', quality=90)
    
    # Compare original and resaved image
    resaved_im = Image.open(temp_path)
    diff = ImageChops.difference(im, resaved_im)
    
    # Calculate extreme differences (bright spots = tampering)
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0: max_diff = 1
    scale = 255.0 / max_diff
    
    diff = ImageChops.constant(diff, scale) # Amplify differences
    
    # Calculate fraud score based on brightness
    stat = np.array(diff).mean()
    os.remove(temp_path)
    return stat > 5.0  # Threshold: >5 usually indicates manipulation

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'document' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['document']
    path = "uploaded_doc.jpg"
    file.save(path)

    # Layer 1: Forensic Analysis (ELA)
    is_tampered = perform_ela(path)

    # Layer 2: Text Analysis (OCR)
    results = reader.readtext(path)
    text = " ".join([res[1].lower() for res in results])

    # Final Logic
    status = "Correct"
    reason = "Document passed all security checks."
    
    if is_tampered:
        status = "Fraud"
        reason = "Digital manipulation detected in image pixels (ELA Analysis)."
    elif any(word in text for word in ["void", "sample", "copy", "specimen"]):
        status = "Fraud"
        reason = "Document contains restricted watermarks (VOID/SAMPLE)."
    elif len(text) < 10:
        status = "Fraud"
        reason = "Document text is unreadable or non-existent."

    os.remove(path)
    return jsonify({"status": status, "reason": reason})

if __name__ == '__main__':
    app.run(de
            bug=True)
