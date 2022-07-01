#!/bin/sh

for filename in ./tests/payloads/*.json; do

	curl -L -F \"upload_file=@$filename\" http://localhost:8888/productionplan | python -m json.tool
	printf '\n\n'
done

curl -L -F \"upload_file=@./tests/payloads/payload1.json http://localhost:8888/productionplan | python -m json.tool
