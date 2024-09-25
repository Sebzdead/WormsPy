from app import app
import werkzeug.middleware.profiler as wmp

app.config['PROFILE'] = True
app.wsgi_app = wmp.ProfilerMiddleware(app.wsgi_app, restrictions=[10])
app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)