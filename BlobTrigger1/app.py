import logging
from azure.storage.blob import BlobServiceClient
import azure.functions as func
import json
import time
from requests import get, post
import os
import requests
from collections import OrderedDict
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, flash, redirect, url_for, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Initializing flask app
app = Flask(__name__)
cors = CORS(app)

# azure account with document intelligence and storage account
'''
endpoint = "https://nanfungdocint.cognitiveservices.azure.com/"
apim_key = "d292acca02da47a2a2afb8265aec2ff6"
storage_account_name = "openaitestdata"
storage_account_key = "ONYG9hw5vN4iqmsQWQ3bPF1MKX0SOghFZ7JstrbBD/8+XDduYLawrsPJvwNkKU7PhC4S+RgjqB33+AStuMN7Iw=="
'''

storage_service = "openaitestdata"
storage_api_key = "ONYG9hw5vN4iqmsQWQ3bPF1MKX0SOghFZ7JstrbBD/8+XDduYLawrsPJvwNkKU7PhC4S+RgjqB33+AStuMN7Iw=="
doc_container = "nanfungocrdemo"


# Route for seeing a data
# @app.route('/api/v2/upload', methods=["GET"])
@app.route('/healthcheck', methods=["GET"])
def healthcheck():
    # Returning an api for showing in reactjs
    return {"status": "OK"}

'''
@app.route('/')
def index():
    return 'Index Page'


@app.route('/hello')
def hello():
    return 'Hello, World'

@app.route('/upload')
def upload():
   return 
       #<form action = "http://localhost:5000/uploader" method = "POST" 
       #enctype = "multipart/form-data">
       #input type = "file" name = "file" />
       #<input type = "submit"/>
       #</form> 

@app.route('/uploader')
def uploader():
   return "Result"

@app.route('/upload')
def upload_file():
   return render_template('upload.html')


@app.route('/uploader', methods = ['GET', 'POST'])
def save_file():
   if request.method == 'POST':
      f = request.files['file']
      f.save(secure_filename(f.filename))
      return 'file uploaded successfully'
      # return f
'''

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                # Create the BlobServiceClient object
                blob_service_client = BlobServiceClient(account_url=f"https://{storage_service}.blob.core.windows.net/", credential=storage_api_key)
                container_client = blob_service_client.get_container_client(doc_container)
                blob_client = container_client.get_blob_client(filename)
                blob_client.upload_blob(file, overwrite=True)
                url = blob_client.url
                return jsonify({
                        "filename":filename,
                        "url": url
                    }, success=True)
            except:
                return jsonify(success=False)



'''
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(uploaded_file.filename)
    return redirect(url_for('index'))
'''

# Running app
if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='127.0.0.1', debug=True)