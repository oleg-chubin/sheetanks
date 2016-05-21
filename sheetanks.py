from aiohttp import web
import jinja2
import aiohttp_jinja2
import os
import forms

PROJECT_DIR = os.path.dirname(__file__)


@aiohttp_jinja2.template('landing_page.html')
async def handle(request):
    form = forms.LoginForm()
    name = request.match_info.get('name', "Anonymous")
    return {"name": name, 'form': form}

app = web.Application()
aiohttp_jinja2.setup(app,
    loader=jinja2.FileSystemLoader(
        os.path.join(PROJECT_DIR, 'templates')
    )
)

app.router.add_route('GET', '/{name}', handle)
app.router.add_static('/static', os.path.join(PROJECT_DIR, 'static'))

web.run_app(app)
