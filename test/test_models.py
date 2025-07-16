from datetime import datetime

# clase usuario
class usuario:
    def __init__(self, alias, name, car_plate=None):
        if not alias or not name:
            raise ValueError("alias y nombre son obligatorios")
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

# clase viaje
class viaje:
    def __init__(self, rideDateAndTime, finalAddress, allowedSpaces, rideDriver, status="ready", participants=None, rideId=None):
        if not rideDateAndTime or not finalAddress or allowedSpaces < 1 or not rideDriver:
            raise ValueError("campos obligatorios del viaje no validos")
        self.rideDateAndTime = rideDateAndTime
        self.finalAddress = finalAddress
        self.allowedSpaces = allowedSpaces
        self.rideDriver = rideDriver
        self.status = status
        self.participants = participants if participants else []
        self.id = rideId

    def to_dict(self):
        return {
            "id": self.id,
            "rideDateAndTime": self.rideDateAndTime.isoformat() if self.rideDateAndTime else None,
            "finalAddress": self.finalAddress,
            "allowedSpaces": self.allowedSpaces,
            "rideDriver": self.rideDriver.to_dict() if hasattr(self.rideDriver, "to_dict") else self.rideDriver,
            "status": self.status,
            "participants": [p.to_dict() for p in self.participants]
        }

# clase participacion
class participacion:
    def __init__(self, confirmation, destination, occupiedSpaces, participant, status="waiting"):
        if not destination or occupiedSpaces < 1 or not participant:
            raise ValueError("campos invalidos en la participacion")
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
            "participant": self.participant.to_dict() if hasattr(self.participant, "to_dict") else self.participant,
            "status": self.status
        }

# pruebas unitarias
import unittest

class pruebas(unittest.TestCase):

    def test_exito_usuario(self):
        # crear usuario con datos validos
        u = usuario(alias="ana", name="ana lopez", car_plate="XYZ-999")
        self.assertEqual(u.to_dict()["car_plate"], "XYZ-999")

    def test_error_usuario_sin_nombre(self):
        # error por falta de nombre
        with self.assertRaises(ValueError):
            usuario(alias="ana", name="")

    def test_error_viaje_sin_direccion(self):
        # error por direccion final vacia
        u = usuario(alias="juan", name="juan")
        with self.assertRaises(ValueError):
            viaje(datetime(2025, 1, 1, 10), "", 3, u)

    def test_error_participacion_espacios_invalidos(self):
        # error por espacios ocupados invalidos
        u = usuario(alias="mario", name="mario")
        with self.assertRaises(ValueError):
            participacion(datetime(2025, 1, 1, 9), "av lima", 0, u)

if __name__ == "__main__":
    unittest.main()
