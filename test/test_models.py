import unittest
from datetime import datetime
import sys
import os

from src.models.app import User


class usuario_tests(unittest.TestCase):

    def test_exito_usuario_completo(self):
        # prueba de éxito: se crea un usuario con todos los campos
        usuario = User(alias="usuario1", name="juan", car_plate="abc-123")
        self.assertEqual(usuario.alias, "usuario1")
        self.assertEqual(usuario.name, "juan")
        self.assertEqual(usuario.car_plate, "abc-123")
        self.assertEqual(usuario.rides, [])

    def test_error_usuario_dict_sin_placa(self):
        # error controlado: el campo car_plate debe ser none si no se proporciona
        usuario = User(alias="usuario1", name="juan")
        esperado = {
            "alias": "usuario1",
            "name": "juan",
            "car_plate": None
        }
        self.assertEqual(usuario.to_dict(), esperado)

    def test_error_usuario_dict_con_placa(self):
        # error controlado: verificar que el diccionario incluya correctamente la placa
        usuario = User(alias="usuario1", name="juan", car_plate="abc-123")
        esperado = {
            "alias": "usuario1",
            "name": "juan",
            "car_plate": "abc-123"
        }
        self.assertEqual(usuario.to_dict(), esperado)

    def test_error_usuario_sin_placa(self):
        # error controlado: crear usuario sin placa y validar que sea none
        usuario = User(alias="usuario2", name="ana")
        self.assertEqual(usuario.alias, "usuario2")
        self.assertEqual(usuario.name, "ana")
        self.assertIsNone(usuario.car_plate)
        self.assertEqual(usuario.rides, [])


if __name__ == '__main__':
    unittest.main()
