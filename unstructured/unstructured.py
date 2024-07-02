
# Before calling the API, replace filename and ensure sdk is installed: "pip install unstructured-client"
# See https://docs.unstructured.io/api-reference/api-services/sdk for more details

import unstructured_client
import os, sys 
from unstructured_client.models import operations, shared
import json

client = unstructured_client.UnstructuredClient(
    api_key_auth=os.environ["UNSTRUCTURED_API_KEY"],
    server_url="https://api.unstructuredapp.io",
) 
if len(sys.argv) < 2:
    print("Usage: python unstructured.py <filename>")
    sys.exit(1)
filename = sys.argv[1] 
if not os.path.exists(filename):
    print(f"File {filename} does not exist")
    sys.exit(1)

with open(filename, "rb") as f:
    data = f.read()

req = operations.PartitionRequest(
    partition_parameters=shared.PartitionParameters(
        files=shared.Files(
            content=data,
            file_name=filename,
        ),
        # --- Other partition parameters ---
        # Note: Defining 'strategy', 'chunking_strategy', and 'output_format'
        # parameters as strings is accepted, but will not pass strict type checking. It is
        # advised to use the defined enum classes as shown below.
        strategy=shared.Strategy.AUTO,  
        languages=['eng'],
    ),
)

try:
    res = client.general.partition(request=req)

    # Save to JSON file
    output_filename = filename+".json"
    with open(output_filename, "w") as json_file:
        json.dump(res.elements, json_file, indent=4)
    
except Exception as e:
    print(e)

