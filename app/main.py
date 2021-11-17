from flask import Flask, request, jsonify
from flask_cors import CORS

from .utils import get_shop_data

app = Flask(__name__)
CORS(app)


@app.route("/store-data", methods=["POST"])
def store_data():
    body = request.json
    if "username" not in body or "password" not in body or "region" not in body:
        return jsonify({"error": "Missing required field(s)"}), 200
    try:
        return jsonify(
            get_shop_data(body["username"], body["password"], body["region"])
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 200


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Restful API is running!"})
