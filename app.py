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
from datetime import datetime

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
            current_time = datetime.now().strftime("%Y%m%d%H%M%S")
            name, extension = os.path.splitext(filename)
            new_filename = f"{name}_{current_time}{extension}"
            
            try:
                # Create the BlobServiceClient object
                blob_service_client = BlobServiceClient(account_url=f"https://{storage_service}.blob.core.windows.net/", credential=storage_api_key)
                container_client = blob_service_client.get_container_client(doc_container)
                blob_client = container_client.get_blob_client(new_filename)
                # blob_client.upload_blob(file, overwrite=True, content_type=ContentSettings(content_type='application/pdf'))
                blob_client.upload_blob(file, overwrite=True, content_type='application/pdf')
                url = blob_client.url
                return jsonify({
                        "filename":new_filename,
                        "url": url
                    }, success=True)
            except:
                return jsonify(success=False)

@app.route('/run_func', methods=['GET', 'POST'])
def run_func(myblob: func.InputStream, outputDocument: func.Out[func.Document]):
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {myblob.name}\n"
                 f"Blob Size: {myblob.length} bytes")

    # azure account with document intelligence and storage account
    endpoint = "https://nanfungdocint.cognitiveservices.azure.com/"
    apim_key = "d292acca02da47a2a2afb8265aec2ff6"
    storage_account_name = "openaitestdata"
    storage_account_key = "ONYG9hw5vN4iqmsQWQ3bPF1MKX0SOghFZ7JstrbBD/8+XDduYLawrsPJvwNkKU7PhC4S+RgjqB33+AStuMN7Iw=="
        
    model_id = "modelnf2"
    post_url = endpoint + f"/formrecognizer/documentModels/{model_id}:analyze?api-version=2023-07-31"
    # Ref: https://westus2.dev.cognitive.microsoft.com/docs/services/form-recognizer-api-2023-07-31/operations/GetAnalyzeDocumentResult
    headers = {
            # Request headers
            'Content-Type': 'application/pdf',
            'Ocp-Apim-Subscription-Key': apim_key,
        }
    source = myblob.read()
    
    # Query the service and get the returned data
    resp = requests.post(url=post_url, data=source, headers=headers)
    if resp.status_code != 202:
        print("POST analyze failed:\n%s" % resp.text)
        quit()
    print("POST analyze succeeded:\n%s" % resp.headers)
    get_url = resp.headers["operation-location"]

    wait_sec = 10
    logging.info(f"waiting {wait_sec} seconds ...")
    time.sleep(wait_sec)
    logging.info(f"finish waiting ...")
    # The layout API is async therefore the wait statement

    text1 = os.path.basename(myblob.name)
    resp = requests.get(url=get_url, headers={"Ocp-Apim-Subscription-Key": apim_key})
    decoded_content = resp.text.encode('cp950', errors='ignore').decode('cp950')
    resp_json = json.loads(decoded_content)
    logging.info(resp_json)
    status = resp_json["status"]
    logging.info(f"response status: {status}")

    if status == "succeeded":
        print("GET Analysis succeeded:\n%s")
        results = resp_json
    else:
        print("GET Layout results failed:\n%s")
        quit()

    results = resp_json
    
    # Parses the returned Document Intelligence response, constructs a .csv file, and uploads it to the output container
    key_value_dict = results['analyzeResult']['documents'][0]['fields']
    cleaned_key_value_dict = {
        "FileName": myblob.name,
        "DueDate":key_value_dict.get("DueDate", {}).get("valueString", "Not Applicable"),
        "InvoiceDate":key_value_dict.get("InvoiceDate", {}).get("valueString", "Not Applicable"),
        "InvoiceTotal":key_value_dict.get("InvoiceTotal", {}).get("valueString", "Not Applicable"),
        "AmountDue":key_value_dict.get("AmountDue", {}).get("valueString", "Not Applicable"),
        "ContactPerson":key_value_dict.get("ContactPerson", {}).get("valueString", "Not Applicable"),
        "Email":key_value_dict.get("Email", {}).get("valueString", "Not Applicable"),
        "VendorName":key_value_dict.get("VendorName", {}).get("valueString", "Not Applicable"),
        "VendorAddress":key_value_dict.get("VendorAddress", {}).get("valueString", "Not Applicable"),
        "InvoiceId":key_value_dict.get("InvoiceId", {}).get("valueString", "Not Applicable"),
        "URL": "https://openaitestdata.blob.core.windows.net/"+myblob.name
        }
        
    print(cleaned_key_value_dict)
    df = pd.DataFrame([cleaned_key_value_dict])
    outputDocument.set(func.Document.from_dict(cleaned_key_value_dict))
    logging.info("Finished !!!")

# Running app
if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='127.0.0.1', debug=True)
