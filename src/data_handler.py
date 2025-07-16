import json


class DataHandler:
    def __init__(self, filename='data.json'):
        self.filename = filename

        self.dict_entities = {
            "entities": [],
            "User":[],
            "Ride":[]
        }
        self.load_data()

    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.dict_entities, f)

    def load_data(self):
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                for k in data.keys():
                    self.dict_entities[k] = data.get(k, [])
        except FileNotFoundError:
            for k in self.dict_entities.keys():
                self.dict_entities[k] = []

    def add_entity(self, name_entity, entity):
        if name_entity not in self.dict_entities:
            self.dict_entities[name_entity] = []
        if hasattr(entity, 'to_dict') and callable(entity.to_dict):
            self.dict_entities[name_entity].append(entity.to_dict())
        elif isinstance(entity, dict):
            self.dict_entities[name_entity].append(entity)
        else:
            raise TypeError("Entidad no válida: debe ser un dict o tener .to_dict()")


    def _get_by_filter(self, entities,filters):
        filtered_tasks = entities
        for key, value in filters.items():
            filtered_tasks = [t for t in filtered_tasks if t.get(key) == value]
        return filtered_tasks

    def _delete_by_filter(self, entities, filters):
        entities = [t for t in entities if not all(t.get(k) == v for k, v in filters.items())]
        return entities

    def _update_by_filter(self, entities, filters, updates):
        for task in entities:
            if all(task.get(k) == v for k, v in filters.items()):
                task.update(updates)
        return entities

    def get_entities_filter(self, name_entity, filters):
        if name_entity in self.dict_entities:
            return self._get_by_filter(self.dict_entities[name_entity], filters)

    def delete_entity_filter(self, name_entity, filters):
        if name_entity in self.dict_entities:
            self.dict_entities[name_entity] = self._delete_by_filter(self.dict_entities[name_entity], filters)

    def update_entity_filter(self, name_entity, filters, updates):
        if name_entity in self.dict_entities:
            self.dict_entities[name_entity] = self._update_by_filter(self.dict_entities[name_entity], filters, updates)



    def get_entities(self, name_entity):
        if name_entity in self.dict_entities:
            return self.dict_entities[name_entity]
        return None

    def __del__(self):
        self.save_data()
