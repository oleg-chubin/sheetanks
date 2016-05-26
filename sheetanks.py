from aiohttp import web
import jinja2
import aiohttp_jinja2
import aiohttp
from aiohttp_session import get_session, session_middleware, SimpleCookieStorage
import os
import forms
import collections
from uuid import uuid4
from arena import Arena
from avatar import Avatar


TEAM_SIZE = 2
PROJECT_DIR = os.path.dirname(__file__)


ARENAS = {}
BATTLE_QUEUE = collections.deque()


@aiohttp_jinja2.template('landing_page.html')
async def index_handle(request):
    form = forms.LoginForm()
    name = request.match_info.get('name', "Anonymous")
    return {"name": name, 'form': form}


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
            session['vehicle'] = form.data['vehicle']
            return aiohttp.web.HTTPFound('/prebattle')
    else:
        form = forms.HangarForm()
    return {'name': name, 'form': form}


@aiohttp_jinja2.template('arena.html')
async def arena_handle(request):
    arena_id = request.match_info.get('arena_id', None)

    session = await get_session(request)
    session['arena_id'] = arena_id

    name = session.get('name', 'Anonymous')
    return {'name': name}


@aiohttp_jinja2.template('prebattle.html')
async def prebattle_handle(request):
    return {'people_number': len(BATTLE_QUEUE)}


def get_rosters(queue):
    if len(queue) < 2 * TEAM_SIZE:
        return []
    roster = [queue.popleft() for _ in range(2 * TEAM_SIZE)]
    return roster


async def prebattle_ws_handler(request):
    session = await get_session(request)
    account_id = session['account_id']
    name = session['name']
    vehicle = session['vehicle']

    ws = web.WebSocketResponse()

    avatar = Avatar(account_id, name)
    avatar.set_vehicle(vehicle)
    BATTLE_QUEUE.append(avatar),
    avatar.connect(ws)

    await ws.prepare(request)

    roster = get_rosters(BATTLE_QUEUE)
    while roster:
        arena = Arena(teams=[roster[::2], roster[1::2]])
        ARENAS[arena.id] = arena

        for a in roster:
            a.send_message({'redirect': '/arena/{}'.format(arena.id)})
            a.disconnect()

        roster = get_rosters(BATTLE_QUEUE)

    for avatar in BATTLE_QUEUE:
        avatar.send_message(
            {'message': 'People awaiting: {}'.format(len(BATTLE_QUEUE))}
        )

    async for msg in ws:
        if msg.tp == aiohttp.MsgType.text:
            if msg.data == 'close':
                await ws.close()
        elif msg.tp == aiohttp.MsgType.error:
            print('ws connection closed with exception %s' % ws.exception())

    if avatar in BATTLE_QUEUE:
        BATTLE_QUEUE.remove(avatar)

    return ws


WEB_SOCKETS = {}
async def arena_ws_handler(request):
    session = await get_session(request)
    arena_id = session.get('arena_id', None)
    account_id = session['account_id']

    ws = web.WebSocketResponse()

    arena = ARENAS[arena_id]

    await ws.prepare(request)
    arena.connect_avatar(account_id, ws)

    async for msg in ws:
        if msg.tp == aiohttp.MsgType.text:
            if msg.data == 'close':
                await ws.close()
            else:
                arena.got_data(account_id, msg.data)

        elif msg.tp == aiohttp.MsgType.error:
            print('ws connection closed with exception %s' %
                  ws.exception())

    arena.disconnect_avatar(account_id)

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

app.router.add_route('GET', '/', index_handle)
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
