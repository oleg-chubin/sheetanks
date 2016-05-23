import json
import asyncio
from uuid import uuid4


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

    def disconnect(self, ws):
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
        self.avatars = avatars
        self.teams = [[self.avatars[i] for i in team] for team in teams]
        self.turn_data = []
        self.status = 'set_vehicle'
        self.id = str(uuid4())
        self.future = asyncio.Future()
        asyncio.ensure_future(self.turn_rotator(self.future))

    def connect_avatar(self, account_id, ws):
        self.avatars[account_id].connect(ws)

    def disconnect_avatar(self, account_id, ws):
        self.avatars[account_id].disconnect()

    def got_data(self, account_id, data):
        getattr(self, self.status)(account_id, json.loads(data))

    def get_field_position(self, data):
        return {'x': data['x'], 'y': data['y']}

    def set_vehicle(self, account_id, data):
        my_team = self.get_ally(account_id)
        self.vehicles[account_id] = self.get_field_position(data)
        data = {k: v for k, v in self.vehicles.items() if k in my_team}
        for avatar in my_team:
            avatar.send_message(
                {'command': "update_vehicles", "vehicles": data}
            )

    def battle(self, account_id, data):
        self.turn_data.append({'avatar': self.avatars[account_id], 'data': data})

    async def turn_rotator(self, future):
        await asyncio.sleep(TURN_PERIOD)

        print ("sync arena")
        self.sync_arena()

        self.status = 'battle'
        for i in range(MAX_TURN_NUMBER):
            await asyncio.sleep(TURN_PERIOD)

            winner = {}
            for data in self.turn_data:
                if not winner or float(winner['data']) < float(data['data']):
                    winner = data
            print ("winner", winner)
            self.turn_data = []
            for avatar in self.avatars:
                if not winner:
                    msg = 'nooone has won'
                elif avatar.ws == winner['ws']:
                    msg = 'You have won'
                else:
                    msg = '{name} on {vehicle} has won with {data}'.format(
                        vehicle=avatar.vehicle, **winner)
                avatar.send_message({'message': msg})

    def sync_arena(self):
        for ally, enemy in (arena['teams'], reversed(arena['teams'])):
            data = {
                'command': "sync_arena",
                'ally': {k: vehicles[k] for k in ally if k in vehicles},
                'enemy': {k: vehicles[k] for k in enemy if k in vehicles}
            }
            for acc in ally:
                print ("sync", acc)
                data['account_id'] = acc
                arena['ws'][acc].send_str(json.dumps(data))
