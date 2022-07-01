from fastapi import FastAPI, File, UploadFile
import json

from .solver import find_best_powers

app = FastAPI(debug=True)


@app.post("/productionplan/")
def create_upload_files(upload_file: UploadFile = File(...)):
    print(upload_file.file)
    json_data = json.load(upload_file.file)
    return find_best_powers(json_data)

