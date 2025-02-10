from flask import Blueprint, current_app, redirect
from flask.templating import render_template
from flask_jwt_extended import get_jwt_identity, unset_jwt_cookies, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt import ExpiredSignatureError

blueprint = Blueprint('public_routes', __name__)
db = current_app.db

@blueprint.route("/")
def index():
    """
    Returns the index HTML page
    :return:
    """
    try:
        verify_jwt_in_request()
        user = get_jwt_identity()
    except (NoAuthorizationError, ExpiredSignatureError):
        user = None

    if user is None:  # not logged in, redirect to landing page
        return redirect("/landing", code=302)
    else:
        return render_template('index.html', app_name=current_app.config['APP_NAME'])


@blueprint.route("/landing")
def landing():
    """
    Returns the landing HTML page
    :return:
    """
    return render_template('landing-page.html', app_name=current_app.config['APP_NAME'])


@blueprint.route("/favicon.ico")
def send_favicon():
    """
    Returns the favicon for the website
    :return:
    """
    return current_app.send_static_file("favicon.ico")

@blueprint.route("/login")
def login():
    """
    Returns the login HTML page
    :return:
    """
    try:
        verify_jwt_in_request()
        user = get_jwt_identity()
    except (NoAuthorizationError, ExpiredSignatureError):
        user = None

    if user is not None:  # already logged in
        return redirect("/", 302)
    else:
        return render_template('login.html', app_name=current_app.config['APP_NAME'])

@blueprint.route("/register")
def register():
    """
    Returns the register HTML page
    :return:
    """
    try:
        verify_jwt_in_request()
        user = get_jwt_identity()
    except (NoAuthorizationError, ExpiredSignatureError):
        user = None

    if user is not None:  # user already logged in
        return redirect("/", 302)
    else:
        return render_template('register.html', app_name=current_app.config['APP_NAME'])

@blueprint.route("/password-reset")
def password_reset():
    """
    Returns the password reset HTML page
    :return:
    """
    try:
        verify_jwt_in_request()
        user = get_jwt_identity()
    except (NoAuthorizationError, ExpiredSignatureError):
        user = None

    if user is not None:
        return redirect("/", 302)
    else:
        return render_template('password-reset.html', app_name=current_app.config['APP_NAME'])

@blueprint.route("/logout")
def logout():
    """
    User-friendly logout page. Unsets the JWT cookies and redirects to the landing page
    :return:
    """
    response = redirect("/landing", 302)
    unset_jwt_cookies(response)
    return response