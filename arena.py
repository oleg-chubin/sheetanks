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
        self.shots = []
        self.turn_data = {}
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
        self.avatars[account_id].vehicle.set_position(
            self.get_field_position(data))

        data = {k.id: k.vehicle.info for k in my_team if k.vehicle.position}

        for avatar in my_team:
            avatar.send_message(
                {'command': "update_vehicles", "vehicles": data}
            )

    def battle(self, account_id, data):
        avatar = self.avatars[account_id]
        data = self.get_field_position(data)
        self.turn_data[avatar.id] = data
        avatar.send_message(
            {'command': "update_shot", "data": data}
        )

    def broadcast_message(self, data):
        for avatar in chain.from_iterable(self.teams):
            avatar.send_message(data)

    def calculate_turn_result(self, turn_data, divider):
        result = {}

        for ally, enemy in [self.teams, reversed(self.teams)]:
            for avatar in ally:
                if avatar.id not in turn_data:
                    continue

                click_info = turn_data[avatar.id]
                shot = self.get_shot_coords(
                    divider, click_info['x'], click_info['y'])
                for enemy_avatar in enemy:
                    if not enemy_avatar.vehicle.is_alive:
                        continue

                    d2 = (
                        (enemy_avatar.vehicle.position['x'] - shot['x']) ** 2 +
                        (enemy_avatar.vehicle.position['y'] - shot['y']) ** 2
                    )
                    if d2 < avatar.vehicle.info['radius'] ** 2:
                        enemy_avatar.vehicle.decr_hp(avatar.vehicle.info['damage'])

                result.setdefault(avatar.id, {}).update(shot)
        return turn_data

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

            self.shots.append(
                self.calculate_turn_result(self.turn_data, self.divider)
            )
            self.turn_data = {}

            self.sync_arena()
            await self.countdown_turn(2)

            self.divider = self.get_divider()

            for avatar in chain.from_iterable(self.teams):
                avatar.send_message({'message': "msg"})

    def get_divider(self):
        normalized_coords = []
        for avatar in chain.from_iterable(self.teams):
            normalized_coords.append(
                (
                    avatar.vehicle.position['x'] - 500,
                    avatar.vehicle.position['y'] - 500
                )
            )

        x_offset = -500
        for x, y in normalized_coords:
            x_offset = max(x_offset, x / max(abs(y), 20) * 500)

        result = random.randrange(int(x_offset) + 1, -int(x_offset))
        return result

    def get_shot_coords(self, x0, xclick, yclick):
        if not x0:
            return {'x': xclick, 'y': yclick}

        y0 = 500
        x1 = xclick - 500
        y1 = 500 - yclick


        x = (2 * y1 + x1 * (y0 / x0 + x0 / y0))/(y0 / x0 + x0 / y0)
        y = -(x0 / y0 * x + (y1 + x0 / y0 *x1))

        return {'x': 500 - x, 'y': 500 - y}

    def sync_arena(self):
        for ally, enemy in [self.teams, self.teams[::-1]]:
            data = {
                'command': "sync_arena",
                'divider': self.divider,
                'ally': {k.id: k.vehicle.info for k in ally if k.vehicle.position},
                'enemy': {k.id: k.vehicle.info for k in enemy if k.vehicle.position},
                'shots': {
                    'ally': [
                        {"position": s[k.id], "alpha": 100 - i * 20}
                        for i, s in enumerate(reversed(self.shots[-5:]))
                        for k in ally if k.id in s],
                    'enemy': [
                        {"position": s[k.id], "alpha": 100 - i * 20}
                        for i, s in enumerate(reversed(self.shots[-5:]))
                        for k in enemy if k.id in s],
                },
            }
            for avatar in ally:
                avatar.send_message(data)
