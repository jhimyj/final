from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest

from src.data_handler import DataHandler
from src.class_error import NotFound, BusinessValidacion
from src.service import Service
from datetime import datetime
from typing import List, Optional

app = Flask(__name__)
data_handler = DataHandler()
service = Service(data_handler)


class RideParticipation:
    def __init__(
            self,
            confirmation: datetime,
            destination: str,
            occupiedSpaces: int,
            participant: 'User',
            status: str = "waiting"
    ):
        self.confirmation = confirmation
        self.destination = destination
        self.occupiedSpaces = occupiedSpaces
        self.participant = participant
        self.status = status

    def to_dict(self):
        return {
            "confirmation": self.confirmation.isoformat(),
            "destination": self.destination,
            "occupiedSpaces": self.occupiedSpaces,
            "participant": self.participant.to_dict(),
            "status": self.status
        }


class Ride:
    def __init__(
            self,
            rideDateAndTime: datetime,
            finalAddress: str,
            allowedSpaces: int,
            rideDriver: 'User',
            status: str = "ready",
            participants: Optional[List['RideParticipation']] = None,
            rideId: Optional[int] = None
    ):
        self.id = rideId
        self.rideDateAndTime = rideDateAndTime
        self.finalAddress = finalAddress
        self.allowedSpaces = allowedSpaces
        self.rideDriver = rideDriver
        self.status = status
        self.participants = participants if participants else []

    def to_dict(self):
        return {
            "id": self.id,
            "rideDateAndTime": self.rideDateAndTime.isoformat(),
            "finalAddress": self.finalAddress,
            "allowedSpaces": self.allowedSpaces,
            "rideDriver": self.rideDriver.to_dict(),
            "status": self.status,
            "participants": [
                p.to_dict() if hasattr(p, "to_dict") else p for p in self.participants
            ]
        }


class User:
    def __init__(self, alias: str, name: str, car_plate: Optional[str] = None):
        self.alias = alias
        self.name = name
        self.car_plate = car_plate
        self.rides: List['RideParticipation'] = []

    def to_dict(self):
        return {
            "alias": self.alias,
            "name": self.name,
            "car_plate": self.car_plate
        }


def handler_error(error):
    if isinstance(error, NotFound):
        return jsonify({"error": str(error)}), 404
    if isinstance(error, BusinessValidacion):
        return jsonify({"error": str(error)}), 422
    if isinstance(error, BadRequest):
        return jsonify({"error": str(error)}), 400
    return jsonify({"error": str(error)}), 500


@app.route('/All/User', methods=['GET'])
def get_all_users():
    try:
        users = data_handler.get_entities("User")
        if users is None or not isinstance(users, list):
            return jsonify({"error": "No se pudo obtener la lista de usuarios."}), 500
        if len(users) == 0:
            return jsonify({"message": "No hay usuarios registrados actualmente.", "usuarios": []}), 200
        return jsonify({"message": "Todos los Usuarios", "usuarios": users}), 200
    except Exception as e:
        return jsonify({"error": "Error interno al obtener usuarios", "detalle": str(e)}), 500


@app.route('/Create/User', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body provided"}), 400

        alias = data.get('alias')
        name = data.get('name')
        car_plate = data.get('car_plate')

        if not alias or not name:
            return jsonify({"error": "Alias and name are required"}), 400

        users = data_handler.get_entities("User") or []
        for user in users:
            if user.get("alias") == alias:
                raise BusinessValidacion("El alias ya está registrado")

        new_user = User(alias=alias, name=name, car_plate=car_plate)
        data_handler.add_entity("User", new_user)
        data_handler.save_data()

        return jsonify({
            "message": "Usuario creado correctamente",
            "usuario": {
                "alias": new_user.alias,
                "name": new_user.name,
                "car_plate": new_user.car_plate
            }
        }), 201

    except Exception as error:
        return handler_error(error)


@app.route('/Crear/Ride', methods=['POST'])
def crearViaje():
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se envió información"}), 400

        fechaHora = datos.get("fechaHora")
        direccion = datos.get("direccion")
        espacios = datos.get("espacios")
        aliasConductor = datos.get("conductor")
        estado = datos.get("estado", "ready")

        if not all([fechaHora, direccion, espacios, aliasConductor]):
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        try:
            fechaHora = datetime.fromisoformat(fechaHora)
        except ValueError:
            return jsonify({"error": "La fecha no tiene el formato correcto"}), 400

        if estado not in ["ready", "inprogress", "done"]:
            return jsonify({"error": "Estado no permitido"}), 400

        listaUsuarios = data_handler.get_entities("User") or []
        datosConductor = next((u for u in listaUsuarios if u["alias"] == aliasConductor), None)
        if not datosConductor:
            return jsonify({"error": "Conductor no encontrado"}), 404

        conductor = User(
            alias=datosConductor["alias"],
            name=datosConductor["name"],
            car_plate=datosConductor.get("car_plate")
        )

        listaViajes = data_handler.get_entities("Ride") or []
        nuevoId = max([v.get("id", 0) for v in listaViajes if isinstance(v, dict)], default=0) + 1

        viaje = Ride(
            rideDateAndTime=fechaHora,
            finalAddress=direccion,
            allowedSpaces=int(espacios),
            rideDriver=conductor,
            status=estado,
            rideId=nuevoId
        )

        data_handler.add_entity("Ride", viaje)
        data_handler.save_data()

        return jsonify({
            "mensaje": "Viaje creado con exito",
            "viaje": viaje.to_dict()
        }), 201

    except Exception as error:
        return handler_error(error)


@app.route('/usuarios/<alias>/rides', methods=['GET'])
def obtenerViajesPorUsuario(alias):
    try:
        listaViajes = data_handler.get_entities("Ride") or []

        viajesDelUsuario = [
            ride for ride in listaViajes
            if ride.get("rideDriver", {}).get("alias") == alias
        ]

        return jsonify({
            "mensaje": f"Se encontraron {len(viajesDelUsuario)} viaje(s) del usuario '{alias}'",
            "viajes": viajesDelUsuario
        }), 200

    except Exception as error:
        return handler_error(error)


@app.route('/usuarios/<alias>/rides/<int:rideId>', methods=['GET'])
def obtenerRideConEstadisticas(alias, rideId):
    try:
        listaViajes = data_handler.get_entities("Ride") or []

        ride = next(
            (r for r in listaViajes
             if r.get("id") == rideId and r.get("rideDriver", {}).get("alias") == alias),
            None
        )

        if not ride:
            return jsonify({"error": "Ride no encontrado para ese usuario"}), 404

        participantes = ride.get("participants", [])

        for p in participantes:
            aliasParticipante = p.get("participant", {}).get("alias")
            estadisticas = {
                "previousRidesTotal": 0,
                "previousRidesCompleted": 0,
                "previousRidesMissing": 0,
                "previousRidesNotMarked": 0,
                "previousRidesRejected": 0
            }

            todosLosViajes = data_handler.get_entities("Ride") or []
            for otroRide in todosLosViajes:
                for participacion in otroRide.get("participants", []):
                    part = participacion.get("participant", {})
                    if part.get("alias") == aliasParticipante:
                        estadisticas["previousRidesTotal"] += 1
                        estado = participacion.get("status")
                        if estado == "completed":
                            estadisticas["previousRidesCompleted"] += 1
                        elif estado == "missing":
                            estadisticas["previousRidesMissing"] += 1
                        elif estado == "not_marked":
                            estadisticas["previousRidesNotMarked"] += 1
                        elif estado == "rejected":
                            estadisticas["previousRidesRejected"] += 1

            p["participant"].update(estadisticas)

        respuesta = {
            "ride": {
                "id": ride.get("id"),
                "rideDateAndTime": ride.get("rideDateAndTime"),
                "finalAddress": ride.get("finalAddress"),
                "driver": alias,
                "status": ride.get("status"),
                "participants": participantes
            }
        }

        return jsonify(respuesta), 200

    except Exception as error:
        return handler_error(error)


@app.route('/rides/<int:rideId>/join', methods=['POST'])
def join_ride(rideId):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se envió información"}), 400

        alias = data.get("alias")
        destination = data.get("destination")
        occupiedSpaces = data.get("occupiedSpaces", 1)

        if not alias or not destination:
            return jsonify({"error": "Alias y destino son requeridos"}), 400

        listaViajes = data_handler.get_entities("Ride") or []
        ride = next((r for r in listaViajes if r.get("id") == rideId), None)

        if not ride:
            return jsonify({"error": "Viaje no encontrado"}), 404

        listaUsuarios = data_handler.get_entities("User") or []
        datosUsuario = next((u for u in listaUsuarios if u["alias"] == alias), None)

        if not datosUsuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        espaciosOcupados = sum(p.get("occupiedSpaces", 1) for p in ride.get("participants", []))
        if espaciosOcupados + occupiedSpaces > ride.get("allowedSpaces"):
            return jsonify({"error": "No hay espacios suficientes disponibles"}), 422

        usuario = User(
            alias=datosUsuario["alias"],
            name=datosUsuario["name"],
            car_plate=datosUsuario.get("car_plate")
        )

        participation = RideParticipation(
            confirmation=datetime.now(),
            destination=destination,
            occupiedSpaces=occupiedSpaces,
            participant=usuario,
            status="confirmed"
        )

        ride["participants"].append(participation.to_dict())
        data_handler.save_data()

        return jsonify({
            "mensaje": "Te has unido al viaje exitosamente",
            "participacion": participation.to_dict()
        }), 201

    except Exception as error:
        return handler_error(error)


@app.route('/rides/<int:rideId>/participants/<alias>/status', methods=['PUT'])
def update_participant_status(rideId, alias):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se envió información"}), 400

        new_status = data.get("status")
        valid_statuses = ["waiting", "rejected", "confirmed", "missing", "not_marked", "inprogress", "done"]

        if new_status not in valid_statuses:
            return jsonify({"error": f"Estado no válido. Estados permitidos: {valid_statuses}"}), 400

        listaViajes = data_handler.get_entities("Ride") or []
        ride = next((r for r in listaViajes if r.get("id") == rideId), None)

        if not ride:
            return jsonify({"error": "Viaje no encontrado"}), 404

        participantes = ride.get("participants", [])
        participante_encontrado = False

        for p in participantes:
            if p.get("participant", {}).get("alias") == alias:
                p["status"] = new_status
                participante_encontrado = True
                break

        if not participante_encontrado:
            return jsonify({"error": "Participante no encontrado en este viaje"}), 404

        data_handler.save_data()

        return jsonify({
            "mensaje": "Estado del participante actualizado exitosamente",
            "alias": alias,
            "nuevo_estado": new_status
        }), 200

    except Exception as error:
        return handler_error(error)


@app.route('/', methods=['GET'])
def dummy_endpoint():
    try:
        saludo = service.saludar()
        return jsonify({"saludo": saludo})
    except Exception as e:
        return handler_error(e)


if __name__ == '__main__':
    app.run(debug=True)
