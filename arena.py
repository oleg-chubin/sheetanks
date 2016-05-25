import json
import asyncio
from uuid import uuid4
from itertools import chain
import random


MAX_TURN_NUMBER = 5
TURN_PERIOD = 20


class Arena():
    def __init__(self, teams):
        self.teams = teams
        self.turn_data = []
        self.vehicles = {}
        self.status = 'set_vehicle'
        self.id = str(uuid4())
        self.divider = None
        self.future = asyncio.Future()
        asyncio.ensure_future(self.turn_rotator(self.future))

    @property
    def avatars(self):
        return {a.id: a for a in chain.from_iterable(self.teams)}

    def connect_avatar(self, account_id, ws):
        self.avatars[account_id].connect(ws)

    def disconnect_avatar(self, account_id):
        self.avatars[account_id].disconnect()

    def got_data(self, account_id, data):
        getattr(self, self.status)(account_id, json.loads(data))

    def get_field_position(self, data):
        return {
            'x': 1000 * data['x'] / float(data['width']),
            'y': 1000 * data['y'] / float(data['height'])
        }

    def get_ally(self, account_id):
        if account_id in [i.id for i in self.teams[0]]:
            return self.teams[0]
        return self.teams[1]

    def set_vehicle(self, account_id, data):
        my_team = self.get_ally(account_id)
        self.vehicles[account_id] = self.get_field_position(data)

        data = {k.id: self.vehicles[k.id] for k in my_team if k.id in self.vehicles}

        for avatar in my_team:
            avatar.send_message(
                {'command': "update_vehicles", "vehicles": data}
            )

    def battle(self, account_id, data):
        avatar = self.avatars[account_id]
        data = self.get_field_position(data)
        self.turn_data.append({'avatar': avatar, 'data': data})
        print("updateshot", data)
        avatar.send_message(
            {'command': "update_shot", "data": data}
        )

    def broadcast_message(self, data):
        for avatar in chain.from_iterable(self.teams):
            avatar.send_message(data)

    async def countdown_turn(self, delay):
        for i in range(delay, 0, -1):
            self.broadcast_message({'command': "update_countdown", "left": i})
            await asyncio.sleep(1)

    async def turn_rotator(self, future):
        await self.countdown_turn(TURN_PERIOD)

        self.status = 'battle'
        for i in range(MAX_TURN_NUMBER):
            self.sync_arena()

            await self.countdown_turn(TURN_PERIOD)

            print (self.turn_data)
            self.turn_data = []
            self.divider = self.get_divider()

            for avatar in chain.from_iterable(self.teams):
                avatar.send_message({'message': "msg"})

    def get_divider(self):
        normalized_coords = []
        for vehicle in self.vehicles.values():
            normalized_coords.append((vehicle['x'] - 500, vehicle['y'] - 500))
        max_x = 400
        min_x = -400
        for x, y in normalized_coords:
            if x * y < 0:
                min_x = max(min_x, x / y * 100)
            elif  x * y > 0:
                max_x = min(max_x, x / y * 100)

        print(normalized_coords, min_x, max_x)
        result = random.randrange(int(min_x) + 1, int(max_x))
        if not result:
            result = None
        else:
            result = 100.0 / result

        print(normalized_coords, min_x, max_x, result)
        return result

    def sync_arena(self):
        for ally, enemy in [self.teams, self.teams[::-1]]:
            data = {
                'command': "sync_arena",
                'divider': self.divider,
                'ally': {k.id: self.vehicles[k.id] for k in ally if k.id in self.vehicles},
                'enemy': {k.id: self.vehicles[k.id] for k in enemy if k.id in self.vehicles}
            }
            for avatar in ally:
                avatar.send_message(data)
