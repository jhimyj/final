from datetime import datetime
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
