from datetime import datetime
from typing import List, Optional
from enum import Enum


class RideStatus(Enum):
    READY = "ready"
    INPROGRESS = "inprogress"
    DONE = "done"


class ParticipationStatus(Enum):
    WAITING = "waiting"
    REJECTED = "rejected"
    CONFIRMED = "confirmed"
    MISSING = "missing"
    NOTMARKED = "notmarked"
    INPROGRESS = "inprogress"
    DONE = "done"


class RideParticipation:
    def _init_(self, confirmation: datetime, destination: str,
               occupied_spaces: int, status: ParticipationStatus):
        self.confirmation = confirmation
        self.destination = destination
        self.occupied_spaces = occupied_spaces
        self.status = status


class User:
    def _init_(self, alias: str, name: str, car_plate: Optional[str] = None):
        self.alias = alias
        self.name = name
        self.car_plate = car_plate  
        self.rides: List['Ride'] = []


class Ride:
    def _init_(self, ride_date_and_time: datetime, final_address: str,
               allowed_spaces: int, ride_driver: User, status: RideStatus):
        self.ride_date_and_time = ride_date_and_time
        self.final_address = final_address
        self.allowed_spaces = allowed_spaces
        self.ride_driver = ride_driver
        self.status = status
        self.participants: List[RideParticipation] = []


class DataHandler:
    def _init_(self):
        self.users: List[User] = []
        self.rides: List[Ride] = []

    def add_user(self, user: User):
        self.users.append(user)

    def add_ride(self, ride: Ride):
        self.rides.append(ride)

    def get_user_by_alias(self, alias: str) -> Optional[User]:
        for user in self.users:
            if user.alias == alias:
                return user
        return None

    def get_rides_by_driver(self, driver: User) -> List[Ride]:
        return [ride for ride in self.rides if ride.ride_driver == driver]


if _name_ == "_main_":
    data_handler = DataHandler()

    driver = User("john_doe", "John Doe", "ABC-123")
    passenger = User("jane_smith", "Jane Smith")

    data_handler.add_user(driver)
    data_handler.add_user(passenger)

    ride_date = datetime(2024, 7, 20, 8, 0) 
    ride = Ride(ride_date, "Downtown Office", 4, driver, RideStatus.READY)

    participation = RideParticipation(
        confirmation=datetime.now(),
        destination="Downtown Office",
        occupied_spaces=1,
        status=ParticipationStatus.CONFIRMED
    )

    ride.participants.append(participation)
    data_handler.add_ride(ride)

    print(f"Usuario creado: {driver.name} con placa {driver.car_plate}")
    print(f"Viaje creado para: {ride.ride_date_and_time} a {ride.final_address}")
    print(f"Espacios disponibles: {ride.allowed_spaces}")
    print(f"Estado del viaje: {ride.status.value}")
    print(f"Participantes: {len(ride.participants)}")
