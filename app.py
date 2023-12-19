import logging
from azure.storage.blob import BlobServiceClient, ContentSettings
import azure.functions as func
import json
import time
import os
import requests
from requests import get, post
from collections import OrderedDict
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, flash, redirect, url_for, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import re

# Initializing flask app
app = Flask(__name__)
cors = CORS(app)
app.secret_key = "super secret key"

# azure account with document intelligence and storage account
'''
endpoint = "https://nanfungdocint.cognitiveservices.azure.com/"
apim_key = "d292acca02da47a2a2afb8265aec2ff6"
storage_account_name = "openaitestdata"
storage_account_key = "ONYG9hw5vN4iqmsQWQ3bPF1MKX0SOghFZ7JstrbBD/8+XDduYLawrsPJvwNkKU7PhC4S+RgjqB33+AStuMN7Iw=="
'''

storage_service = "openaitestdata"
storage_api_key = "ONYG9hw5vN4iqmsQWQ3bPF1MKX0SOghFZ7JstrbBD/8+XDduYLawrsPJvwNkKU7PhC4S+RgjqB33+AStuMN7Iw=="
doc_container = "input"


@app.route('/')
def index():
   print('Request for index page received')
   return render_template('index.html')

# Route for seeing a data
# @app.route('/api/v2/upload', methods=["GET"])
@app.route('/healthcheck', methods=["GET"])
def healthcheck():
    # Returning an api for showing in reactjs
    return {"status": "OK"}

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
                blob_client.upload_blob(file, overwrite=True, content_type='application/pdf')
                url = blob_client.url
                return jsonify({
                        "filename":filename,
                        "url": url
                    }, success=True)
            except:
                return jsonify(success=False)
            

# Running app
if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='127.0.0.1', debug=True)
