import json
import asyncio
from uuid import uuid4
from itertools import chain


MAX_TURN_NUMBER = 5
TURN_PERIOD = 20


class Vehicle():
    def __init__(self, vehicle):
        pass


class Avatar():
    def __init__(self, account_id, name):
        self.id = account_id
        self.name = name
        self.connected = False
        self.postponed_messages = []

    def set_vehicle(self, vehicle):
        self.vehicle = Vehicle(vehicle)

    def disconnect(self):
        self.connected = False
        self.ws = None

    def connect(self, ws):
        self.connected = True
        self.ws = ws
        for data in self.postponed_messages:
            ws.send_str(data)
        self.postponed_messages = []

    def send_message(self, data):
        message = {"account_id": self.id, 'name': self.name}
        message.update(data)
        message = json.dumps(message)

        if self.connected:
            self.ws.send_str(message)
        else:
            self.postponed.append(message)


class Arena():
    def __init__(self, avatars, teams):
        self.avatars = {x.id: x for x in avatars}
        self.teams = [[avatars[i].id for i in team] for team in teams]
        self.turn_data = []
        self.vehicles = {}
        self.status = 'set_vehicle'
        self.id = str(uuid4())
        self.future = asyncio.Future()
        asyncio.ensure_future(self.turn_rotator(self.future))

    def connect_avatar(self, account_id, ws):
        self.avatars[account_id].connect(ws)

    def disconnect_avatar(self, account_id):
        self.avatars[account_id].disconnect()

    def got_data(self, account_id, data):
        getattr(self, self.status)(account_id, json.loads(data))

    def get_field_position(self, data):
        return {'x': data['x'], 'y': data['y']}

    def get_ally(self, account_id):
        if account_id in self.teams[0]:
            return self.teams[0]
        return self.teams[1]

    def set_vehicle(self, account_id, data):
        my_team = self.get_ally(account_id)
        self.vehicles[account_id] = self.get_field_position(data)
        data = {k: v for k, v in self.vehicles.items() if k in my_team}
        for avatar_id in my_team:
            self.avatars[avatar_id].send_message(
                {'command': "update_vehicles", "vehicles": data}
            )

    def battle(self, account_id, data):
        self.turn_data.append({'avatar': self.avatars[account_id], 'data': data})

    async def turn_rotator(self, future):
        await asyncio.sleep(TURN_PERIOD)

        print("sync arena")
        self.sync_arena()

        self.status = 'battle'
        for i in range(MAX_TURN_NUMBER):
            await asyncio.sleep(TURN_PERIOD)

            winner = {}
            for data in self.turn_data:
                if not winner or float(winner['data']) < float(data['data']):
                    winner = data
            print("winner", winner)
            self.turn_data = []
            for avatar in self.avatars.values():
                if not winner:
                    msg = 'nooone has won'
                elif avatar.ws == winner['ws']:
                    msg = 'You have won'
                else:
                    msg = '{name} on {vehicle} has won with {data}'.format(
                        vehicle=avatar.vehicle, **winner)
                avatar.send_message({'message': msg})

    def sync_arena(self):
        ally, enemy = self.teams
        data = {
            'command': "sync_arena",
            'ally': {k: self.vehicles[k] for k in ally if k in self.vehicles},
            'enemy': {k: self.vehicles[k] for k in enemy if k in self.vehicles}
        }
        for acc in chain(ally, enemy):
            print("sync", acc)
            self.avatars[acc].send_message(data)
