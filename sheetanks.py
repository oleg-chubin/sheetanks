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
app.router.add_static('/static', os.path.join(PROJECT_DIR, 'static'))

web.run_app(app)
