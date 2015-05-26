from flask import Flask, session, request, make_response, url_for, redirect,\
    render_template, abort, jsonify, current_app
import requests
import json
from datetime import datetime, timedelta
import os
import logging
from logging.handlers import RotatingFileHandler

import config


app = Flask(__name__)
app.config['SECRET_KEY'] = config.secret_key


# configure logging for this app
def configure_logging(app):

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s '
                                  '[in %(pathname)s:%(lineno)d]')

    # Also error can be sent out via email.
    # So we can also have a SMTPHandler?
    log_file = os.path.join(os.path.dirname(__file__), 'audio-anno.log')

    max_size = 1024 * 1024 * 20  # Max Size for a log file: 20MB
    log_handler = RotatingFileHandler(log_file, maxBytes=max_size,
                                      backupCount=10)

    try:
        if config.LOG_LEVEL:
            log_level = config.LOG_LEVEL
        else:
            log_level = 'DEBUG'
    except AttributeError:
        log_level = 'DEBUG'

    log_handler.setLevel(log_level)
    log_handler.setFormatter(formatter)

    app.logger.addHandler(log_handler)


configure_logging(app)


@app.route("/")
def index():

    if 'auth_tok' in session:
        app.logger.debug("User is logged in : %s" % session['auth_tok'])
	logging.debug("User is logged in")
	current_app.logger.debug("User is logged in!")
        auth_tok = session['auth_tok']

        # check if it has expired
        oauth_token_expires_in_endpoint = config.swtstoreURL +\
            '/oauth/token-expires-in'
        resp = requests.get(oauth_token_expires_in_endpoint,
                            proxies=config.PROXIES)
        expires_in = json.loads(resp.text)['expires_in']

        check = datetime.utcnow() - auth_tok['issued']
        if check > timedelta(seconds=expires_in):
            app.logger.debug('access token expired')
            auth_tok = {'access_token': '', 'refresh_token': ''}
        else:
            app.logger.debug('access token did not expire')

    else:
        app.logger.debug("User is not logged in!")
        auth_tok = {'access_token': '', 'refresh_token': ''}

    return render_template('index.html',
                           access_token=auth_tok['access_token'],
                           refresh_token=auth_tok['refresh_token'],
                           config=config)


@app.route('/pages')
def start_page():
    return render_template('/pages/startpage.html')


@app.route('/experiments')
def render_explist():
    return render_template('pages/experiments.html')


@app.route('/pages/contact')
def contact():
    return render_template('pages/contact/contact.html')


@app.route("/downloadMusic")
def downloadMusic():

    url = request.args.get("url")
    app.logger.debug("in downloadMusic with content : %s" % url)
    url = url.strip()
    music_file_parse_url = url.split("/")
    music_file_name = music_file_parse_url[-1]
    app.logger.debug("Music file name: %s" % music_file_name)
    music_file_path = os.path.join(os.path.dirname(__file__), 'static/music_files/',
				  music_file_name)
    app.logger.debug("Music file path: %s" % music_file_path)
    try:
        response = requests.get(url, proxies=config.PROXIES)
        data = response.content
    except Exception, e:
        app.logger.debug('Error downloading the music file: %s' % e)
        app.logger.debug(e)
	print 'here'
        abort(500)

    try:
        open(music_file_path, 'wb').write(data)
    except Exception, e:
        app.logger.debug('error writing file')
	print 'there'
	print e
        abort(500)

        music_file_url = url_for('static', filename='music_files/' + music_file_name)
    return make_response(music_file_url, 200)

@app.route("/authenticate")
def authenticateWithOAuth():

    auth_tok = None
    code = request.args.get('code')
    app.logger.debug('recvd code: %s' % code)

    # prepare the payload
    payload = {
        'scopes': 'email sweet',
        'client_secret': config.app_secret,
        'code': code,
        'redirect_uri': config.redirect_uri,
        'grant_type': 'authorization_code',
        'client_id': config.app_id
    }

    # token exchange endpoint
    oauth_token_x_endpoint = config.swtstoreURL + '/oauth/token'
    resp = requests.post(oauth_token_x_endpoint, data=payload,
                         proxies=config.PROXIES)
    auth_tok = json.loads(resp.text)
    app.logger.debug('recvd auth token from swtstore')
    app.logger.debug(auth_tok)

    if 'error' in auth_tok:
        app.logger.debug(auth_tok['error'])
        return make_response(auth_tok['error'], 200)

    # set sessions etc
    session['auth_tok'] = auth_tok
    session['auth_tok']['issued'] = datetime.utcnow()

    return redirect(url_for('index'))


@app.route("/signOut")
def signOut():
    user = request.args.get("user")

    app.logger.debug("in sign out the user %s" % user)
    app.logger.debug(session)
    if 'auth_tok' in session:
        del(session['auth_tok'])
    app.logger.debug('session deleted')
    app.logger.debug(session)
    app.logger.debug('new session above')

    return redirect(url_for('index'))


@app.errorhandler(404)
def render_404(err):
    return render_template('errors/404.html', error=err.description)


@app.errorhandler(400)
def bad_request(err):
    return make_response(jsonify({'error': err.description}), 400)

if __name__ == "__main__":

    app.debug = True
    app.run(host='0.0.0.0',  port=5003)
