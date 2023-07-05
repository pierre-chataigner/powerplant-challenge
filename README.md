Powerplant-coding-challenge solution
==============
A solution to 
<a href="https://github.com/gem-spaas/powerplant-coding-challenge">ENGIE powerplant coding challenge</a> 

**Author:** *Pierre Chataigner*
 

# Building the environment
The code works with python 3.9 or greater version. An environment is needed with Flask==2.3.2
The requirement.txt file can be used to build it with pip or poetry.

## Running the API 
### With docker
Permission are needed to execute the following commands.
```
docker build -t powerplant
docker run -ti -p 8888:8888 powerplant
```

### Without docker
Once the environement is build and activated, the API can be started with the following command
```
flask --app main run -p 8888 --host=0.0.0.0
```
Now the API is open on localhost:8888

## Send requests
Here's an example of request to test the API :
```
curl -H "Content-Type: application/json" --data @path/to/your/payload.json http://localhost:8888/productionplan
```

