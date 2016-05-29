import json
import asyncio
from conf import settings
from uuid import uuid4
from itertools import chain


MAX_TURN_NUMBER = 5
TURN_PERIOD = 20


class Vehicle():
    def __init__(self, vehicle, **kwargs):
        self._data = {}
        for k, v in settings.vehicles[vehicle].items():
            self._data[k] = v
        self._data.update(kwargs)
        self._data['initial_hp'] = self._data['hp']
        self._data['alive'] = True

    @property
    def is_alive(self):
        return self._data['alive']

    def set_position(self, pos):
        self._data.update(pos)

    @property
    def position(self):
        if 'x' not in self._data or 'y' not in self._data:
            return None
        return {'x': self._data['x'], 'y': self._data['y']}

    @property
    def info(self):
        return self._data.copy()

    def decr_hp(self, value):
        self._data['hp'] -= value
        self._data['alive'] = self._data['hp'] < 0
