


from flask import Flask,url_for,redirect,session,request
from flask_oauth import OAuth
from flask_login import LoginManager, login_required

import opml
from user import User

app = Flask(__name__)
login_manager = LoginManager()
login_manager.setup_app(app)

oauth = OAuth()

twitter = oauth.remote_app('twitter',
    base_url='https://api.twitter.com/1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key='12Jbo5GoDxd6dq6epffIQ',
    consumer_secret='00rIgEhKD944U3vt5vZdh0fXO4hEmQWY7vPOuyN7E',
)

#if not app.debug:
    #import logging
    #from themodule import TheHandlerYouWant
    #file_handler = TheHandlerYouWant(...)
    #file_handler.setLevel(logging.WARNING)
    #app.logger.addHandler(file_handler)

# Flask-Login support
# http://packages.python.org/Flask-Login/

@login_manager.user_loader
def load_user(userid):
    return User.get(userid)

@app.route('/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    session['twitter_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    session['twitter_user'] = resp['screen_name']

    flash('You were signed in as %s' % resp['screen_name'])
    return redirect(next_url)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # login and validate the user...
        login_user(user)
        flash("Logged in successfully.")
        return redirect(request.args.get("next") or url_for("index"))
    return render_template("login.html", form=form)

@app.route("/settings")
@login_required
def settings():
    pass

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(somewhere)

@twitter.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')

@app.route("/tweet")
def status():
    resp = twitter.get('statuses/home_timeline.json')
    if resp.status == 200:
        tweets = resp.data
    else:
        tweets = None
        flash('Unable to load tweets from Twitter. Maybe out of '
          'API calls or Twitter is overloaded.')

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run(debug=True)
