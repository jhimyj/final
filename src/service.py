from data_handler import DataHandler
from src.class_error import NotFound, BusinessValidacion




class Service:
    """
    aca toda la logica de negocio
    """

    def __init__(self, data_handler: DataHandler):
        self.data_handler = data_handler

    def saludar(self):
        return "hola mundo!"
    def get_users(self):
        return self.data_handler.get_entities("users")




