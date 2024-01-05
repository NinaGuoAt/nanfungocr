import logging
from azure.storage.blob import BlobServiceClient, ContentSettings
import azure.functions as func
import json
import time
from requests import get, post
import os
import requests
from collections import OrderedDict
import numpy as np
import pandas as pd

# This part is automatically generated
def main(myblob: func.InputStream, outputDocument: func.Out[func.Document]):
# def main(myblob: func.InputStream, outputDocument):
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {myblob.name}\n"
                 f"Blob Size: {myblob.length} bytes")

    # azure account with document intelligence and storage account
    endpoint = "https://nanfungdocint.cognitiveservices.azure.com/"
    apim_key = "d292acca02da47a2a2afb8265aec2ff6"
    storage_account_name = "openaitestdata"
    storage_account_key = "ONYG9hw5vN4iqmsQWQ3bPF1MKX0SOghFZ7JstrbBD/8+XDduYLawrsPJvwNkKU7PhC4S+RgjqB33+AStuMN7Iw=="
        
    model_id = "modelnf2"
    # model_id = "modelnf"
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
    # resp_json = json.loads(resp.text.encode(encoding = 'utf-8', errors='ignore'))
    resp_json = json.loads(decoded_content)
    logging.info(resp_json)
    status = resp_json["status"]
    logging.info(f"response status: {status}")

    if status == "succeeded":
        print("GET Analysis succeeded:\n%s")
        results = resp_json
        # logging.info(f"response result: {results}")
    else:
        print("GET Layout results failed:\n%s")
        quit()

    results = resp_json

    # This is the connection to the blob storage, with the Azure Python SDK
    # output_container_name = "output"
    # blob_service_client = BlobServiceClient.from_connection_string(f'DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={storage_account_key};EndpointSuffix=core.windows.net')
    # container_client = blob_service_client.get_container_client(output_container_name)
    
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
    
    # Here is the upload to the blob storage
    # tab1_csv = df.to_csv(header=True, index=False, mode='w')
    # name1 = (os.path.splitext(text1)[0]) +'.csv'

    # Upload the results to Azure      
    # container_client.upload_blob(name=name1, data=tab1_csv)
    # outputDocument.set(func.Document.from_dict({"id": name1}))
    outputDocument.set(func.Document.from_dict(cleaned_key_value_dict))
    logging.info("Finished !!!")
    return {"status": "OK"}
           
