import sys

sys.path.append("/usr/src/app/api")
from run import app
from utils.handlers import ExceptionHandler as handler

# global handler exception of application
# app.add_error_handler(Exception, handler.handle_500)

# handler for not found resources
app.add_sink(handler.handle_404, '^((?!static).)*$')
