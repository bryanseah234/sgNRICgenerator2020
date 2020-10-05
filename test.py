import barcode
from flask import Flask, render_template, request, redirect
from flask import *
from flask import send_file, send_from_directory, safe_join, abort
from copy import copy
import barcode
from barcode.writer import ImageWriter
from barcode.codex import Code39
from checksum import is_nric_valid
import os


nric = 't0325316z'
code39 = Code39(nric, add_checksum = False, writer=barcode.writer.ImageWriter())
full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'logo.png')
image = code39.save("/static/image.png")
