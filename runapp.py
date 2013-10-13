from paste.deploy import loadapp
from waitress import serve
import os


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app = loadapp('config:production.ini', relative_to='src/vanity_app')
    if 'STAGING' in os.environ:
        expose_tracebacks=True
    else:
        expose_tracebacks=False
    serve(app, host='0.0.0.0', port=port, expose_tracebacks=expose_tracebacks)
