from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest

from src.data_handler import DataHandler
from src.class_error import NotFound, BusinessValidacion
from src.service import Service

app = Flask(__name__)
data_handler = DataHandler()
service = Service(data_handler)




#aca maeja los errores de sevicio
def handler_error(error):
    if isinstance(error, NotFound):
        return jsonify({"error": str(error)}), 404

    if isinstance(error, BusinessValidacion):
        return jsonify({"error": str(error)}), 422

    if isinstance(error, BadRequest):
        return jsonify({"error": str(error)}), 400

    if isinstance(error, Exception):
        return jsonify({"error": str(error)}), 500




@app.route('/', methods=['GET'])
def dummy_endpoint():
    try:
        saludo = service.saludar()
        return jsonify({"saludo": saludo})
    except Exception as e:
        return handler_error(e)


if __name__ == '__main__':
    app.run(debug=True)

