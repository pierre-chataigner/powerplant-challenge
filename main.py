from flask import Flask, request, jsonify

from solver import calculate_production_plan, get_checks, preprocessing, postprocessing

app = Flask(__name__)


@app.route("/productionplan", methods=["POST"])
def calculate_production_plan_endpoint():
    payload = request.get_json()
    checks = get_checks(payload)
    if not checks[0]:
        return jsonify(checks[1])
    load, fuels, powerplants = preprocessing(
        payload["load"], payload["fuels"], payload["powerplants"]
    )
    production_plan = postprocessing(
        calculate_production_plan(load, fuels, powerplants)
    )
    return jsonify(production_plan)


if __name__ == "__main__":
    app.run()
