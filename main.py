from flask import Flask, render_template, request, redirect
from flask import *
from flask import send_file, send_from_directory, safe_join, abort
from copy import copy
import barcode
from barcode.writer import ImageWriter
from barcode.codex import Code39
from checksum import is_nric_valid
import os
import shutil

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

@app.after_request
def add_header(response):
    response.cache_control.max_age = 100
    return response

@app.route('/', methods=['GET'])
def root():
    path = os.path.join(app.root_path, 'static', 'image.png')
    delete_path = os.path.join(app.root_path, "static")
    error = None
    for i in os.listdir(delete_path):
            if i.startswith('image'):  # not to remove other images
                os.remove(path)
    return render_template("index.html", error=error)

@app.route('/generate', methods=['GET'])
def generate():
    if "nric" in request.args:
        path = os.path.join(app.root_path, 'static', 'image.png')
        delete_path = os.path.join(app.root_path, "static")
        filename = "image" 
        for i in os.listdir(delete_path):
            if i.startswith('image'):  # not to remove other images
                os.remove(path)
        nric = request.args.get('nric')
        print(nric)
        if is_nric_valid(nric) == True:
            code39 = Code39(nric, add_checksum = False, writer=barcode.writer.ImageWriter())
            os.chdir(delete_path)
            image = code39.save(filename)
            # a = os.path.abspath(image)
            # b = delete_path
            # shutil.move(a,b)
            return render_template("barcode.html", nric=nric)
        elif nric == '':
            error = '<Empty Input>'
            return render_template("index.html", error=error)
        else:
            error = '<Invalid NRIC>'
            check = True
            return render_template("index.html", error=error)
    else:
        error = '<Empty Input>'
        return render_template("index.html", error=error)


if __name__ == '__main__':
    app.run(debug=False, use_reloader=True)