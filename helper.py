import pickle
from ast import literal_eval
from os import path
from typing import List


def load_dict_from_file(file_name: str):
    loaded = None
    if path.isfile(file_name):
        # with open(file_name, 'r') as tasks_file:
        #     loaded = dict(literal_eval(tasks_file.read()))
        with open(file_name, 'rb') as tasks_file:
            loaded = pickle.load(tasks_file)
    return loaded


def save_dict_to_file(file_name: str, obj: dict):
    # with open(file_name, 'w') as tasks_file:
    #     tasks_file.write(str(obj))
    with open(file_name, 'wb') as tasks_file:
        pickle.dump(obj, tasks_file)


class BiDict(dict):
    def __init__(self, *args, **kwargs):
        super(BiDict, self).__init__(*args, **kwargs)
        self.inverse = {}
        for key, value in self.items():
            self.inverse.setdefault(value, []).append(key)

    def __setitem__(self, key, value):
        if key in self:
            self.inverse[self[key]].remove(key)
        super(BiDict, self).__setitem__(key, value)
        self.inverse.setdefault(value, []).append(key)

    def __delitem__(self, key):
        value = self[key]
        self.inverse.setdefault(value, []).remove(key)
        if value in self.inverse and not self.inverse[value]:
            del self.inverse[value]
        super(BiDict, self).__delitem__(key)

    def get_inverse(self, value) -> List:
        return self.inverse[value]

    def save(self, file_name: str):
        with open(file_name, 'w') as tasks_file:
            tasks_file.write(str(self))
        # with open(file_name, 'wb') as tasks_file:
        #     pickle.dump(dict(self), tasks_file)

    @staticmethod
    def load(file_name: str):
        if path.isfile(file_name):
            with open(file_name, 'r') as tasks_file:
                loaded = BiDict(literal_eval(tasks_file.read()))
            # with open(file_name, 'rb') as tasks_file:
            #     loaded = BiDict(pickle.load(tasks_file))
        else:
            raise Exception(f"{file_name} does not exist")
        return loaded
