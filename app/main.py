from fastapi import FastAPI, File, UploadFile
import json

from .solver import find_best_powers

app = FastAPI(debug=True)


@app.post("/productionplan/")
def create_upload_files(upload_file: UploadFile = File(...)):
    json_data = json.load(upload_file.file)
    return find_best_powers(json_data)

"""import uvicorn
from fastapi import File, UploadFile, FastAPI

from .solver import find_best_powers

app = FastAPI()

@app.post("/productionplan")
async def upload(file: UploadFile = File(...)):
	print(find_best_powers(file.filename))
	try:
		with open(file.filename, 'r') as f:
			print('hello1')
			return find_best_powers(file.filename)
	except Exception:
		return {"message": "There was an error uploading the file"}
	finally:
		await file.close()
	return {"message": f"Successfuly uploaded {file.filename}"}
	

if __name__ == '__main__':
	uvicorn.run(app, host='0.0.0.0', port=8888)
"""
