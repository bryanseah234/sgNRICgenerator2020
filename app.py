import base64
import io
import os
from flask import Flask, render_template, request
import barcode
from barcode.writer import ImageWriter
from utils import is_nric_valid

app = Flask(__name__, template_folder='templates') 
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_header(response):
    """
    Add headers to prevent caching.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/', methods=['GET'])
def root():
    return render_template("index.html", error=None)

@app.route('/generate', methods=['GET'])
def generate():
    if "nric" in request.args:
        nric = request.args.get('nric', '').strip().upper()
        
        if not nric:
            return render_template("index.html", error='<Empty Input>')
            
        if is_nric_valid(nric):
            # Generate the barcode image in memory instead of saving to disk
            # This makes the app thread-safe and production-ready
            rv = io.BytesIO()
            code39 = barcode.Code39(nric, writer=ImageWriter(), add_checksum=False)
            code39.write(rv)
            
            # Encode image to base64
            image_base64 = base64.b64encode(rv.getvalue()).decode('utf-8')
            
            return render_template("barcode.html", nric=nric, image_base64=image_base64)
        else:
            return render_template("index.html", error='<Invalid NRIC>')
    
    return render_template("index.html", error='<Empty Input>')

if __name__ == '__main__':
    app.run(debug=False)
