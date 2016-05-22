from aiohttp import web
import jinja2
import aiohttp_jinja2
import aiohttp
from aiohttp_session import get_session, session_middleware, SimpleCookieStorage
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import os
import forms
import collections
import json
from uuid import uuid4
import asyncio


TEAM_SIZE = 2
MAX_TURN_NUMBER = 5
TURN_PERIOD = 20
PROJECT_DIR = os.path.dirname(__file__)


@aiohttp_jinja2.template('landing_page.html')
async def handle(request):
    form = forms.LoginForm()
    name = request.match_info.get('name', "Anonymous")
    return {"name": name, 'form': form}


@aiohttp_jinja2.template('landing_page.html')
async def login_handle(request):
    await request.post()
    form = forms.LoginForm(request.POST)
    if form.validate():
        session = await get_session(request)
        session['name'] = form.nickname.data
        session['account_id'] = str(uuid4())
        return aiohttp.web.HTTPFound('/hangar')
    return {"name": form.nickname.object_data, 'form': form}


@aiohttp_jinja2.template('hangar_page.html')
async def hangar_handle(request):
    session = await get_session(request)
    name = session.get('name', 'Anonimous')
    if request.method == 'POST':
        await request.post()
        form = forms.HangarForm(request.POST)
        if form.validate():
            return aiohttp.web.HTTPFound(
                '/prebattle?vehicle={}'.format(form.data['vehicle'])
            )
    else:
        form = forms.HangarForm()
    return {'name': name, 'form': form}


@aiohttp_jinja2.template('arena.html')
async def arena_handle(request):
    arena_id = request.match_info.get('arena_id', None)

    session = await get_session(request)
    session['arena_id'] = arena_id

    name = session.get('name', 'Anonimous')
    return {'name': name}


ARENAS = {}

BATTLE_QUEUE = collections.deque()

VEHICLES = {}


@aiohttp_jinja2.template('prebattle.html')
async def prebattle_handle(request):
    session = await get_session(request)
    account_id = session['account_id']
    VEHICLES[account_id] = request.GET['vehicle']
    return {'people_number': len(BATTLE_QUEUE)}


def get_rosters(queue):
    if len(queue) < 2 * TEAM_SIZE:
        return []
    roster = [queue.popleft() for i in range(2 * TEAM_SIZE)]
    return roster


def sync_arena(arena):
    vehicles = arena['vehicles']
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


async def turn_rotator(future, arena_id):
    arena = ARENAS[arena_id]
    arena['status'] = 'set_vehicle'
    await asyncio.sleep(TURN_PERIOD)

    print ("sync arena")
    sync_arena(arena)

    arena['status'] = 'battle'
    arena.setdefault('turn_data', [])
    for i in range(MAX_TURN_NUMBER):
        await asyncio.sleep(TURN_PERIOD)
        arenas_ws = arena.get('ws', {})

        print ("arena ws", arenas_ws)
        print ("arena turn data", arena['turn_data'])

        winner = {}
        for data in arena['turn_data']:
            if not winner or float(winner['data']) < float(data['data']):
                winner = data
        print ("winner", winner)
        arena['turn_data'] = []
        for ws in arenas_ws.values():
            if not winner:
                msg = 'nooone has won'
            elif ws == winner['ws']:
                msg = 'You have won'
            else:
                msg = '{name} on {vehicle} has won with {data}'.format(
                    vehicle=VEHICLES[winner['account_id']], **winner)
            ws.send_str(msg)


async def prebattle_ws_handler(request):
    session = await get_session(request)
    account_id = session['account_id']

    ws = web.WebSocketResponse()

    BATTLE_QUEUE.append({'account_id': account_id, 'ws': ws})

    await ws.prepare(request)

    roster = get_rosters(BATTLE_QUEUE)
    while roster:
        arena_id = str(uuid4())

        participants = [i['account_id'] for i in roster]
        ARENAS[arena_id] = {'teams': [participants[::2], participants[1::2]]}
        future = asyncio.Future()
        asyncio.ensure_future(turn_rotator(future, arena_id))
        ARENAS[arena_id]['turn_future'] = future

        data = {'redirect': '/arena/{}'.format(arena_id)}
        for web_sock in roster:
            web_sock['ws'].send_str(json.dumps(data))

        roster = get_rosters(BATTLE_QUEUE)

    for web_sock in BATTLE_QUEUE:
        data = {'message': 'People awaiting: {}'.format(len(BATTLE_QUEUE))}
        web_sock['ws'].send_str(json.dumps(data))

    async for msg in ws:
        if msg.tp == aiohttp.MsgType.text:
            if msg.data == 'close':
                await ws.close()
        elif msg.tp == aiohttp.MsgType.error:
            print('ws connection closed with exception %s' % ws.exception())

    if ws in BATTLE_QUEUE:
        BATTLE_QUEUE.remove(ws)

    return ws


def get_field_position(data):
    return {'x': data['x'], 'y': data['y']}


WEB_SOCKETS = {}
async def arena_ws_handler(request):
    session = await get_session(request)
    arena_id = session.get('arena_id', None)
    name = session.get('name', 'Anonimous')
    account_id = session['account_id']

    print("websocket starterd")
    ws = web.WebSocketResponse()

    arena = ARENAS[arena_id]
    arena_websockets = arena.setdefault('ws', {})
    vehicles = arena.setdefault('vehicles', {})
    arena_websockets[account_id] = ws
    my_team = [i for i in arena['teams'] if account_id in i][0]

    await ws.prepare(request)
    print("websocket prepared")

    async for msg in ws:
        print("websocket new msg")
        if msg.tp == aiohttp.MsgType.text:
            if msg.data == 'close':
                await ws.close()
            else:
                if arena['status'] == 'set_vehicle':
                    vehicles[account_id] = get_field_position(json.loads(msg.data))
                    data = {k: v for k, v in vehicles.items() if k in my_team}
                    for acc in my_team:
                        if acc in arena_websockets:
                            arena_websockets[acc].send_str(
                                json.dumps(
                                    {
                                        'command': "update_vehicles",
                                        "vehicles": data,
                                        "account_id": acc
                                    }
                                ))
                elif arena['status'] == 'battle':
                    arena['turn_data'].append(
                        {'name':name, 'account_id': account_id, 'ws': ws, 'data': msg.data}
                    )
        elif msg.tp == aiohttp.MsgType.error:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')
    WEB_SOCKETS[arena_id].pop(id(ws), None)

    return ws


app = web.Application(
    middlewares=[
        session_middleware(
            SimpleCookieStorage()
        )
    ]
)


aiohttp_jinja2.setup(app,
    loader=jinja2.FileSystemLoader(
        os.path.join(PROJECT_DIR, 'templates')
    )
)

app.router.add_route('GET', '/login', handle)
app.router.add_route('POST', '/login', login_handle)
app.router.add_route('GET', '/hangar', hangar_handle)
app.router.add_route('POST', '/hangar', hangar_handle)
app.router.add_route('GET', '/prebattle', prebattle_handle)
app.router.add_route('GET', '/prebattle/ws', prebattle_ws_handler)
app.router.add_route('GET', '/arena/ws', arena_ws_handler)
app.router.add_route('GET', '/arena/{arena_id}', arena_handle)
app.router.add_static('/static', os.path.join(PROJECT_DIR, 'static'), name='static')

web.run_app(app)
