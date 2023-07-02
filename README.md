Powerplant-coding-challenge solution
==============
A solution to 
<a href="https://github.com/gem-spaas/powerplant-coding-challenge">ENGIE powerplant coding challenge</a> 

**Author:** *Pierre Chataigner*
 

# Structure

## Code
The folder "app" contains a "main.py" file containing the API generated with uvicorn and the "solver.py" file which compute the solution.

## Tests
The folder "test" contains several payload.json files. They has been used to test the solution.


# Solution
The solution works with Python 3.8.10 or greater version.

## Running the API 
Open a terminal. If you have permissions you can use docker.
### With docker
You must have permission to execute the following commands.
```
docker build -t powerplant_pierre .
docker run -ti -p 8888:8888 powerplant_pierre
```
Now an API is open on localhost:8888.


### Without docker
First you need to build a python virtual environment :
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Then you start the API with uvicorn :
```
uvicorn app.main:app --host 0.0.0.0 --port 8888
```
Now an API is open on localhost:8888.

## Send requests
Open another terminal. 
You can try it with a post request. For example :
```
curl -L -F "upload_file=@tests/payloads/payload1.json" http://localhost:8888/productionplan | python -m json.tool 
```

If you want to put the solution in a json file, run :
```
curl -L -F "upload_file=@tests/payloads/payload1.json" http://localhost:8888/productionplan | python -m json.tool >> results.json
```



# Additional information

- If you want to run in production, you may want to set ```debug = False``` in the "app/main.py" file.

- The notebook "folder/" has the sole purpose of showing the step for my code to be build, so you can evaluate it if your want. It is not necessary in the execution of the code.

