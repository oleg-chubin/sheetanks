import json
from vehicle import Vehicle


class Avatar():
    def __init__(self, account_id, name):
        self.id = account_id
        self.name = name
        self.connected = False
        self.postponed = []

    def set_vehicle(self, vehicle):
        self.vehicle = Vehicle(vehicle, name=self.name)

    def disconnect(self):
        self.connected = False
        self.ws = None

    def connect(self, ws):
        self.connected = True
        self.ws = ws
        for data in self.postponed:
            ws.send_str(data)
        self.postponed = []

    def send_message(self, data):
        message = {"account_id": self.id, 'name': self.name}
        message.update(data)
        message = json.dumps(message)

        if self.connected:
            self.ws.send_str(message)
        else:
            self.postponed.append(message)
