
sudo docker build -t powerplant_pierre .
sudo docker run -ti -p 8888:8888 powerplant_pierre

uvicorn app.main:app --host 0.0.0.0 --port 8888
chmod 755 tests/test_payloads.sh
curl -L -F "upload_file=@tests/payloads/payload1.json" http://localhost:8888/productionplan | python -m json.tool 
curl -L -F "upload_file=@tests/payloads/payload1.json" http://localhost:8888/productionplan | python -m json.tool >> results.json




Dire qu'il faut mettre debug = False dans l'API dans le main.py s'il veulent le faire tourner en prod

TODO:
-gitignore fichiers cachés
