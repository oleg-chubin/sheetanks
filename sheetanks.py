from aiohttp import web
import jinja2
import aiohttp_jinja2
import os


@aiohttp_jinja2.template('landing_page.html')
async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    return {"name": name}

app = web.Application()
aiohttp_jinja2.setup(app,
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates')
    )
)

app.router.add_route('GET', '/{name}', handle)

web.run_app(app)
