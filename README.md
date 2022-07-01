
TODO : requirements
uvicorn app.main:app --host 0.0.0.0 --port 8888
chmod 755 tests/test_payloads.sh
curl -L -F "upload_file=@tests/payloads/payload1.json" http://localhost:8888/productionplan | python -m json.tool 
curl -L -F "upload_file=@tests/payloads/payload1.json" http://localhost:8888/productionplan | python -m json.tool >> results.json
