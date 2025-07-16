from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest

from src.data_handler import DataHandler
from src.class_error import NotFound, BusinessValidacion
from src.service import Service
from datetime import datetime

app = Flask(__name__)
data_handler = DataHandler()
service = Service(data_handler)


class RideParticipation:
    def __init__(self, confirmation, destination, occupiedSpaces, participant, status="waiting"):
        self.confirmation = confirmation
        self.destination = destination
        self.occupiedSpaces = occupiedSpaces
        self.participant = participant
        self.status = status

    def to_dict(self):
        return {
            "confirmation": self.confirmation.isoformat() if self.confirmation else None,
            "destination": self.destination,
            "occupiedSpaces": self.occupiedSpaces,
            "participant": self.participant.to_dict() if hasattr(self.participant, 'to_dict') else self.participant,
            "status": self.status
        }


class Ride:
    def __init__(self, rideDateAndTime, finalAddress, allowedSpaces, rideDriver, status="ready", participants=None,
                 rideId=None):
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
            "rideDriver": self.rideDriver.to_dict() if hasattr(self.rideDriver, 'to_dict') else self.rideDriver,
            "status": self.status,
            "participants": [p.to_dict() if hasattr(p, "to_dict") else p for p in self.participants]
        }


class User:
    def __init__(self, alias, name, car_plate=None):
        self.alias = alias
        self.name = name
        self.car_plate = car_plate
        self.rides = []

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


@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    try:
        usuarios = data_handler.get_entities("User") or []
        usuarios_dict = []
        for usuario in usuarios:
            if isinstance(usuario, dict):
                usuarios_dict.append(usuario)
            else:
                usuarios_dict.append(usuario.to_dict())

        return jsonify(usuarios_dict), 200
    except Exception as error:
        return handler_error(error)


@app.route('/usuarios/<alias>', methods=['GET'])
def get_usuario(alias):
    try:
        usuarios = data_handler.get_entities("User") or []
        usuario = next((u for u in usuarios if u.get("alias") == alias), None)

        if not usuario:
            raise NotFound(f"Usuario con alias '{alias}' no encontrado")

        return jsonify(usuario), 200
    except Exception as error:
        return handler_error(error)


@app.route('/usuarios/<alias>/rides', methods=['GET'])
def get_rides_by_user(alias):
    try:
        usuarios = data_handler.get_entities("User") or []
        usuario = next((u for u in usuarios if u.get("alias") == alias), None)

        if not usuario:
            raise NotFound(f"Usuario con alias '{alias}' no encontrado")

        rides = data_handler.get_entities("Ride") or []
        rides_usuario = [ride for ride in rides if ride.get("rideDriver", {}).get("alias") == alias]

        return jsonify(rides_usuario), 200
    except Exception as error:
        return handler_error(error)


@app.route('/usuarios/<alias>/rides/<int:rideid>', methods=['GET'])
def get_ride_with_stats(alias, rideid):
    try:
        usuarios = data_handler.get_entities("User") or []
        usuario = next((u for u in usuarios if u.get("alias") == alias), None)

        if not usuario:
            raise NotFound(f"Usuario con alias '{alias}' no encontrado")

        rides = data_handler.get_entities("Ride") or []
        ride = next((r for r in rides if r.get("id") == rideid and r.get("rideDriver", {}).get("alias") == alias), None)

        if not ride:
            raise NotFound(f"Ride con ID {rideid} no encontrado para el usuario {alias}")

        participantes_stats = []
        for p in ride.get("participants", []):
            alias_participante = p.get("participant", {}).get("alias")

            stats = get_stats_participante(alias_participante)

            participante_data = p.get("participant", {}).copy()
            participante_data.update(stats)

            participante_stats = {
                "confirmation": p.get("confirmation"),
                "participant": participante_data,
                "destination": p.get("destination"),
                "occupiedSpaces": p.get("occupiedSpaces"),
                "status": p.get("status")
            }
            participantes_stats.append(participante_stats)

        response = {
            "ride": {
                "id": ride.get("id"),
                "rideDateAndTime": ride.get("rideDateAndTime"),
                "finalAddress": ride.get("finalAddress"),
                "driver": alias,
                "status": ride.get("status"),
                "participants": participantes_stats
            }
        }

        return jsonify(response), 200
    except Exception as error:
        return handler_error(error)


def get_stats_participante(alias_participante):
    stats = {
        "previousRidesTotal": 0,
        "previousRidesCompleted": 0,
        "previousRidesMissing": 0,
        "previousRidesNotMarked": 0,
        "previousRidesRejected": 0
    }

    rides = data_handler.get_entities("Ride") or []
    for ride in rides:
        for participacion in ride.get("participants", []):
            if participacion.get("participant", {}).get("alias") == alias_participante:
                stats["previousRidesTotal"] += 1
                estado = participacion.get("status")
                if estado == "completed":
                    stats["previousRidesCompleted"] += 1
                elif estado == "missing":
                    stats["previousRidesMissing"] += 1
                elif estado == "notmarked":
                    stats["previousRidesNotMarked"] += 1
                elif estado == "rejected":
                    stats["previousRidesRejected"] += 1

    return stats


@app.route('/usuarios/<alias>/rides/<int:rideid>/requestToJoin/<participant_alias>', methods=['POST'])
def request_to_join_ride(alias, rideid, participant_alias):
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No se envió información")

        destino = data.get("destination")
        espacios = data.get("occupiedSpaces", 1)

        if not destino:
            raise BadRequest("El destino es requerido")

        usuarios = data_handler.get_entities("User") or []
        conductor = next((u for u in usuarios if u.get("alias") == alias), None)
        if not conductor:
            raise NotFound(f"Usuario conductor '{alias}' no encontrado")

        participante = next((u for u in usuarios if u.get("alias") == participant_alias), None)
        if not participante:
            raise NotFound(f"Usuario participante '{participant_alias}' no encontrado")

        rides = data_handler.get_entities("Ride") or []
        ride = next((r for r in rides if r.get("id") == rideid and r.get("rideDriver", {}).get("alias") == alias), None)

        if not ride:
            raise NotFound(f"Ride con ID {rideid} no encontrado para el usuario {alias}")

        if ride.get("status") != "ready":
            raise BusinessValidacion("Solo se puede unir a un ride antes de que inicie (status ready)")

        participantes = ride.get("participants", [])
        for p in participantes:
            if p.get("participant", {}).get("alias") == participant_alias:
                raise BusinessValidacion("El participante ya ha solicitado unirse a este ride")

        espacios_ocupados = sum(p.get("occupiedSpaces", 1) for p in participantes)
        if espacios_ocupados + espacios > ride.get("allowedSpaces"):
            raise BusinessValidacion("No hay espacios suficientes disponibles")

        nueva_participacion = {
            "confirmation": None,
            "destination": destino,
            "occupiedSpaces": espacios,
            "participant": participante,
            "status": "waiting"
        }

        ride["participants"].append(nueva_participacion)
        data_handler.save_data()

        return jsonify({"message": "Solicitud para unirse al ride enviada exitosamente",
                        "participacion": nueva_participacion}), 201

    except Exception as error:
        return handler_error(error)


@app.route('/usuarios/<alias>/rides/<int:rideid>/accept/<participant_alias>', methods=['POST'])
def accept_participant(alias, rideid, participant_alias):
    try:
        usuarios = data_handler.get_entities("User") or []
        conductor = next((u for u in usuarios if u.get("alias") == alias), None)
        if not conductor:
            raise NotFound(f"Usuario conductor '{alias}' no encontrado")

        rides = data_handler.get_entities("Ride") or []
        ride = next((r for r in rides if r.get("id") == rideid and r.get("rideDriver", {}).get("alias") == alias), None)

        if not ride:
            raise NotFound(f"Ride con ID {rideid} no encontrado para el usuario {alias}")

        participantes = ride.get("participants", [])
        participacion = None
        for p in participantes:
            if p.get("participant", {}).get("alias") == participant_alias:
                participacion = p
                break

        if not participacion:
            raise NotFound(f"Participante '{participant_alias}' no encontrado en este ride")

        if participacion.get("status") != "waiting":
            raise BusinessValidacion("Solo se puede aceptar una solicitud en estado 'waiting'")

        espacios_ocupados = sum(p.get("occupiedSpaces", 1) for p in participantes if
                                p.get("participant", {}).get("alias") != participant_alias and p.get(
                                    "status") == "confirmed")

        if espacios_ocupados + participacion.get("occupiedSpaces", 1) > ride.get("allowedSpaces"):
            raise BusinessValidacion("No hay espacios suficientes disponibles")

        participacion["status"] = "confirmed"
        participacion["confirmation"] = datetime.now().isoformat()

        data_handler.save_data()

        return jsonify({"message": f"Participante '{participant_alias}' aceptado exitosamente",
                        "participacion": participacion}), 200

    except Exception as error:
        return handler_error(error)


@app.route('/usuarios/<alias>/rides/<int:rideid>/reject/<participant_alias>', methods=['POST'])
def reject_participant(alias, rideid, participant_alias):
    try:
        usuarios = data_handler.get_entities("User") or []
        conductor = next((u for u in usuarios if u.get("alias") == alias), None)
        if not conductor:
            raise NotFound(f"Usuario conductor '{alias}' no encontrado")

        rides = data_handler.get_entities("Ride") or []
        ride = next((r for r in rides if r.get("id") == rideid and r.get("rideDriver", {}).get("alias") == alias), None)

        if not ride:
            raise NotFound(f"Ride con ID {rideid} no encontrado para el usuario {alias}")

        participantes = ride.get("participants", [])
        participacion = None
        for p in participantes:
            if p.get("participant", {}).get("alias") == participant_alias:
                participacion = p
                break

        if not participacion:
            raise NotFound(f"Participante '{participant_alias}' no encontrado en este ride")

        if participacion.get("status") != "waiting":
            raise BusinessValidacion("Solo se puede rechazar una solicitud en estado 'waiting'")

        participacion["status"] = "rejected"

        data_handler.save_data()

        return jsonify({"message": f"Participante '{participant_alias}' rechazado exitosamente",
                        "participacion": participacion}), 200

    except Exception as error:
        return handler_error(error)


@app.route('/usuarios/<alias>/rides/<int:rideid>/start', methods=['POST'])
def start_ride(alias, rideid):
    try:
        data = request.get_json()
        presentes = data.get("presentParticipants", []) if data else []

        usuarios = data_handler.get_entities("User") or []
        conductor = next((u for u in usuarios if u.get("alias") == alias), None)
        if not conductor:
            raise NotFound(f"Usuario conductor '{alias}' no encontrado")

        rides = data_handler.get_entities("Ride") or []
        ride = next((r for r in rides if r.get("id") == rideid and r.get("rideDriver", {}).get("alias") == alias), None)

        if not ride:
            raise NotFound(f"Ride con ID {rideid} no encontrado para el usuario {alias}")

        if ride.get("status") != "ready":
            raise BusinessValidacion("Solo se puede iniciar un ride en estado 'ready'")

        participantes = ride.get("participants", [])
        for p in participantes:
            if p.get("status") not in ["rejected", "confirmed"]:
                raise BusinessValidacion(
                    "Solo se puede iniciar un ride cuando todas las solicitudes estén en estado 'rejected' o 'confirmed'")

        for p in participantes:
            if p.get("status") == "confirmed":
                alias_participante = p.get("participant", {}).get("alias")
                if alias_participante in presentes:
                    p["status"] = "inprogress"
                else:
                    p["status"] = "missing"

        ride["status"] = "inprogress"

        data_handler.save_data()

        return jsonify({"message": "Ride iniciado exitosamente", "ride": ride}), 200

    except Exception as error:
        return handler_error(error)


@app.route('/usuarios/<alias>/rides/<int:rideid>/end', methods=['POST'])
def end_ride(alias, rideid):
    try:
        usuarios = data_handler.get_entities("User") or []
        conductor = next((u for u in usuarios if u.get("alias") == alias), None)
        if not conductor:
            raise NotFound(f"Usuario conductor '{alias}' no encontrado")

        rides = data_handler.get_entities("Ride") or []
        ride = next((r for r in rides if r.get("id") == rideid and r.get("rideDriver", {}).get("alias") == alias), None)

        if not ride:
            raise NotFound(f"Ride con ID {rideid} no encontrado para el usuario {alias}")

        if ride.get("status") != "inprogress":
            raise BusinessValidacion("Solo se puede terminar un ride en estado 'inprogress'")

        participantes = ride.get("participants", [])
        for p in participantes:
            if p.get("status") == "inprogress":
                p["status"] = "notmarked"

        ride["status"] = "completed"

        data_handler.save_data()

        return jsonify({"message": "Ride terminado exitosamente", "ride": ride}), 200

    except Exception as error:
        return handler_error(error)


@app.route('/usuarios/<alias>/rides/<int:rideid>/unloadParticipant', methods=['POST'])
def unload_participant(alias, rideid):
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No se envió información")

        alias_participante = data.get("participantAlias")
        if not alias_participante:
            raise BadRequest("El alias del participante es requerido")

        usuarios = data_handler.get_entities("User") or []
        conductor = next((u for u in usuarios if u.get("alias") == alias), None)
        if not conductor:
            raise NotFound(f"Usuario conductor '{alias}' no encontrado")

        rides = data_handler.get_entities("Ride") or []
        ride = next((r for r in rides if r.get("id") == rideid and r.get("rideDriver", {}).get("alias") == alias), None)

        if not ride:
            raise NotFound(f"Ride con ID {rideid} no encontrado para el usuario {alias}")

        if ride.get("status") != "inprogress":
            raise BusinessValidacion("Solo se puede bajar de un ride en estado 'inprogress'")

        participantes = ride.get("participants", [])
        participacion = None
        for p in participantes:
            if p.get("participant", {}).get("alias") == alias_participante:
                participacion = p
                break

        if not participacion:
            raise NotFound(f"Participante '{alias_participante}' no encontrado en este ride")

        if participacion.get("status") != "inprogress":
            raise BusinessValidacion("Solo se puede bajar un participante en estado 'inprogress'")

        participacion["status"] = "completed"

        data_handler.save_data()

        return jsonify({"message": f"Participante '{alias_participante}' bajó del ride exitosamente",
                        "participacion": participacion}), 200

    except Exception as error:
        return handler_error(error)


@app.route('/rides', methods=['GET'])
def get_active_rides():
    try:
        rides = data_handler.get_entities("Ride") or []
        rides_activos = [ride for ride in rides if ride.get("status") == "ready"]

        return jsonify({"message": f"Se encontraron {len(rides_activos)} rides activos", "rides": rides_activos}), 200

    except Exception as error:
        return handler_error(error)


@app.route('/usuarios', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No se envió información")

        alias = data.get('alias')
        nombre = data.get('name')
        placa = data.get('car_plate')

        if not alias or not nombre:
            raise BadRequest("Alias y nombre son requeridos")

        usuarios = data_handler.get_entities("User") or []
        for usuario in usuarios:
            if usuario.get("alias") == alias:
                raise BusinessValidacion("El alias ya está registrado")

        nuevo_usuario = User(alias=alias, name=nombre, car_plate=placa)
        data_handler.add_entity("User", nuevo_usuario)
        data_handler.save_data()

        return jsonify({"message": "Usuario creado correctamente", "usuario": nuevo_usuario.to_dict()}), 201

    except Exception as error:
        return handler_error(error)


@app.route('/rides', methods=['POST'])
def create_ride():
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No se envió información")

        fecha_ride = data.get("rideDateAndTime")
        direccion = data.get("finalAddress")
        espacios = data.get("allowedSpaces")
        alias_conductor = data.get("driverAlias")

        if not all([fecha_ride, direccion, espacios, alias_conductor]):
            raise BadRequest("Faltan datos obligatorios")

        try:
            fecha_ride = datetime.fromisoformat(fecha_ride)
        except ValueError:
            raise BadRequest("La fecha no tiene el formato correcto")

        usuarios = data_handler.get_entities("User") or []
        conductor_data = next((u for u in usuarios if u.get("alias") == alias_conductor), None)
        if not conductor_data:
            raise NotFound("Conductor no encontrado")

        conductor = User(alias=conductor_data["alias"], name=conductor_data["name"],
                         car_plate=conductor_data.get("car_plate"))

        rides = data_handler.get_entities("Ride") or []
        nuevo_id = max([r.get("id", 0) for r in rides if isinstance(r, dict)], default=0) + 1

        ride = Ride(rideDateAndTime=fecha_ride, finalAddress=direccion, allowedSpaces=int(espacios),
                    rideDriver=conductor, rideId=nuevo_id)

        data_handler.add_entity("Ride", ride)
        data_handler.save_data()

        return jsonify({"message": "Ride creado exitosamente", "ride": ride.to_dict()}), 201

    except Exception as error:
        return handler_error(error)




if __name__ == '__main__':
    app.run(debug=True)