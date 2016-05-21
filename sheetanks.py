from aiohttp import web
import jinja2
import aiohttp_jinja2
import aiohttp
from aiohttp_session import get_session, session_middleware, SimpleCookieStorage
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import os
import forms


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
        return aiohttp.web.HTTPFound('/prebattle')
    return {"name": form.nickname.object_data, 'form': form}


@aiohttp_jinja2.template('hangar_page.html')
async def prebattle_handle(request):
    session = await get_session(request)
    name = session.get('name', 'Anonimous')
    form = forms.HangarForm()
    return {'name': name, 'form': form}


@aiohttp_jinja2.template('arena.html')
async def arena_handle(request):
    session = await get_session(request)
    name = session.get('name', 'Anonimous')
    return {'name': name}


WEB_SOCKETS = {}
async def websocket_handler(request):
    session = await get_session(request)
    name = session.get('name', 'Anonimous')

    print("websocket starterd")
    ws = web.WebSocketResponse()

    WEB_SOCKETS[id(ws)] = ws

    await ws.prepare(request)
    print("websocket prepared")

    async for msg in ws:
        print("websocket new msg")
        if msg.tp == aiohttp.MsgType.text:
            if msg.data == 'close':
                await ws.close()
            else:
                for web_sock in WEB_SOCKETS.values():
                    web_sock.send_str(msg.data + '({})'.format(name))
        elif msg.tp == aiohttp.MsgType.error:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')
    WEB_SOCKETS.pop(id(ws), None)

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
app.router.add_route('GET', '/prebattle', prebattle_handle)
app.router.add_route('POST', '/prebattle', prebattle_handle)
app.router.add_route('GET', '/arena', arena_handle)
app.router.add_route('GET', '/websocket', websocket_handler)
app.router.add_static('/static', os.path.join(PROJECT_DIR, 'static'), name='static')

web.run_app(app)
