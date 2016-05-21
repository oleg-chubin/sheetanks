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


TEAM_SIZE = 2
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
            return aiohttp.web.HTTPFound('/prebattle')
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


@aiohttp_jinja2.template('prebattle.html')
async def prebattle_handle(request):
    return {'people_number': len(BATTLE_QUEUE)}


def get_rosters(queue):
    if len(queue) < 2 * TEAM_SIZE:
        return []
    roster = [queue.popleft() for i in range(2 * TEAM_SIZE)]
    return roster


async def prebattle_ws_handler(request):
    ws = web.WebSocketResponse()

    BATTLE_QUEUE.append(ws)

    await ws.prepare(request)

    roster = True
    while roster:
        roster = get_rosters(BATTLE_QUEUE)
        arena_id = str(uuid4())
        data = {'redirect': '/arena/{}'.format(arena_id)}
        for web_sock in roster:
            web_sock.send_str(json.dumps(data))

    for web_sock in BATTLE_QUEUE:
        data = {'message': 'People awaiting: {}'.format(len(BATTLE_QUEUE))}
        web_sock.send_str(json.dumps(data))

    async for msg in ws:
        if msg.tp == aiohttp.MsgType.text:
            if msg.data == 'close':
                await ws.close()
        elif msg.tp == aiohttp.MsgType.error:
            print('ws connection closed with exception %s' % ws.exception())

    if ws in BATTLE_QUEUE:
        BATTLE_QUEUE.remove(ws)

    return ws


WEB_SOCKETS = {}
async def arena_ws_handler(request):
    session = await get_session(request)
    arena_id = session.get('arena_id', None)
    name = session.get('name', 'Anonimous')

    print("websocket starterd")
    ws = web.WebSocketResponse()

    WEB_SOCKETS.setdefault(arena_id, {})[id(ws)] = ws

    await ws.prepare(request)
    print("websocket prepared")

    async for msg in ws:
        print("websocket new msg")
        if msg.tp == aiohttp.MsgType.text:
            if msg.data == 'close':
                await ws.close()
            else:
                for web_sock in WEB_SOCKETS[arena_id].values():
                    web_sock.send_str(msg.data + '({})'.format(name))
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
