import unittest
import asyncio
import os
import shutil
import json
from src.logic.place_service import PlaceService
from src.data.database import Database

class TestPlaceExtraData(unittest.TestCase):
    def setUp(self):
        # Configura banco de dados de teste isolado
        self.test_dir = "assets/data_test_extra"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

        # Override temporário das configurações de banco (se possível via monkeypatch ou configs globais)
        # Assumindo que o Database usa caminhos fixos ou configuráveis
        # O Database.initialize usa variáveis de ambiente ou hardcoded?
        # Vou tentar setar os atributos da classe Database se existirem, como vi no test anterior
        Database.DB_DIR = self.test_dir
        Database.DB_NAME = "places.db"

        # Inicializa o banco (cria tabelas)
        Database.initialize()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_extra_data_flattening(self):
        async def run_async():
            # 1. Adicionar um lugar com dados extras (price, wifi, checkin)
            new_place = {
                "country": "br",
                "category": "hotel",
                "name": "Hotel Extra",
                "description": "Teste Extra",
                "price": 500,        # Extra
                "wifi": True,        # Extra
                "checkin": "14:00"   # Extra
            }

            await PlaceService.add_place(new_place)

            # 2. Buscar e verificar se os campos extras estão na raiz do dicionário
            places = await PlaceService.get_places("br", "hotel")
            self.assertEqual(len(places), 1)
            place = places[0]

            print(f"DEBUG: Place retrieved: {place}")

            self.assertEqual(place["name"], "Hotel Extra")
            # Verifica se flattened
            self.assertEqual(place.get("price"), 500, "Price should be flattened")
            self.assertEqual(place.get("wifi"), True, "Wifi should be flattened")
            self.assertEqual(place.get("checkin"), "14:00", "Checkin should be flattened")

            # 3. Atualizar um campo extra
            await PlaceService.update_place(place["id"], {"price": 600, "wifi": False})

            # 4. Verificar atualização
            places_updated = await PlaceService.get_places("br", "hotel")
            place_updated = places_updated[0]

            self.assertEqual(place_updated.get("price"), 600, "Price should be updated")
            self.assertEqual(place_updated.get("wifi"), False, "Wifi should be updated")
            self.assertEqual(place_updated.get("checkin"), "14:00", "Checkin should persist")

        asyncio.run(run_async())

if __name__ == '__main__':
    unittest.main()
