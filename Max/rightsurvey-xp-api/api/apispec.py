import sys

sys.path.append("/usr/src/app/api")
from run import app
from core.settings import config
from falcon_swagger_ui import register_swaggerui_app
import pathlib

# Register swagger api route
STATIC_PATH = pathlib.Path(__file__).parent / 'static'
app.add_static_route('/static', str(STATIC_PATH))
register_swaggerui_app(app, config['SWAGGER_UI_URL'], config['SCHEMA_URL'],
                       page_title=config['PAGE_TITLE'],
                       favicon_url=config['FAVICON_URL'],
                       config=config['SWAGGER_CONF'])
