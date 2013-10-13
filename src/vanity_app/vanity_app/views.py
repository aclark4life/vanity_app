from docutils.core import publish_parts
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPMovedPermanently
from pyramid.response import Response
from pyramid.security import authenticated_userid
from pyramid.security import forget
from pyramid.security import remember
from . import config
from . import trove
from . import utils
import colander
import deform
import json
import os
import pprint
import requests
import stripe
import sys
import urlparse


logger = utils.get_logger()


class Bulk(colander.MappingSchema):
    """
        Colander schema for Manage package -> Bulk add
    """
    packages = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextAreaWidget(
            rows=20, cols=120),
        validator=colander.Length(1))


class Mail(colander.MappingSchema):
    """
        Colander schema for Manage site -> Send mail
        (to beta users)
    """
    subject = colander.SchemaNode(colander.String())
    body = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextAreaWidget(
            rows=20, cols=120),
        validator=colander.Length(1))


class Person(colander.MappingSchema):
    """
        Colander schema for Signup -> beta user
    """
    first_name = colander.SchemaNode(colander.String())
    last_name = colander.SchemaNode(colander.String())
    email_address = colander.SchemaNode(
        colander.String(),
        validator=colander.Email())
    github_username = colander.SchemaNode(colander.String())
    classifiers = colander.SchemaNode(
        deform.Set(),
        widget=deform.widget.CheckboxChoiceWidget(
            values=trove.choices))


class Tweet(colander.MappingSchema):
    """
        Colander schema for Manage site -> Send tweet
    """
    tweet = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextAreaWidget(
        rows=5, cols=120),
        validator=colander.Length(1))


# Static files
_favicon = open(os.path.join(config.HERE, 'static', 'img',
    'favicon.ico')).read()
_google_verify = open(os.path.join(config.HERE, 'static',
    'google939eb63a98c6ddc2.html')).read()
_humans = open(os.path.join(config.HERE, 'static',
    'humans.txt')).read()
_robots = open(os.path.join(config.HERE, 'static',
    'robots.txt')).read()


def favicon(request):
    """
        Static file
    """
    return Response(content_type='image/x-icon', body=_favicon)


def google_verify(request):
    """
        Static file
    """
    return Response(content_type='text/html', body=_google_verify)


def humans(request):
    """
        Static file
    """
    return Response(content_type='text/plain', body=_humans)


def robots(request):
    """
        Static file
    """
    return Response(content_type='text/plain', body=_robots)


def buildout_redir(request):  # redir
    """
        Redir for /buildout -> /buildout/
    """
    return HTTPMovedPermanently(location='/buildout/')


def buildout_software_version(request):  # redir
    """
        Redir for '/build/{software}/{version}'
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    software = request.matchdict['software']
    version = request.matchdict['version']
    return HTTPMovedPermanently(location='/buildout/%s/%s' % (software,
        version))


def buildout_software_version_filename(request):  # redir
    """
        Redir for '/build/{software}/{version}/{filename}'
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    software = request.matchdict['software']
    version = request.matchdict['version']
    filename = request.matchdict['filename']
    if filename == 'develop.cfg':
        return HTTPMovedPermanently(location='/buildout/%s/%s-dev' % (software,
            version))
    elif filename == 'zeo.cfg':
        return HTTPMovedPermanently(location='/buildout/%s/%s-zeo' % (software,
            version))
    else:
        return HTTPMovedPermanently(location='/buildout/%s/%s' % (software,
            version))


def contact(request):
    """
        Process Ye Olde Contact Form, based on send mail form in manage_mail
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    appstruct = None
    betacount = utils.get_beta_count()
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    mail = Mail()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    permissions = utils.get_permission_map(request=request)
    submitted = False
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe = \
        utils.get_slot_info(userid)
    # Send mail
    form = deform.Form(mail, buttons=('Send', ))
    if 'Send' in request.POST:  # detect that the submit button was clicked
        controls = request.POST.items()  # get the form controls
        try:
            appstruct = form.validate(controls)  # call validate
        except deform.ValidationFailure, e:  # catch the exception
            return {
                'appstruct': appstruct,
                'betacount': betacount,
                'form': e.render(),
                'followers': followers,
                'fortune': fortune,
#                'freeslot_org': freeslot_org,
#                'freeslot_package': freeslot_package,
                'menu': menu,
                'num_downloads': num_downloads,
                'num_packages': num_packages,
                'num_packages_pypi': num_packages_pypi,
                'num_times_featured': num_times_featured,
#                'package': freeslot_package,
                'permissions': permissions,
                'slotnum_org': slotnum_org,
                'slotnum_org_stripe': slotnum_org_stripe,
                'slotnum_package': slotnum_package,
                'slotnum_package_stripe': slotnum_package_stripe,
                'slots_org': slots_org,
                'slots_package': slots_package,
                'submitted': submitted,
                'userid': userid,
            }  # re-render the form with an exception
        # the form submission succeeded, we have the data
        submitted = True
        body = appstruct['body']
        subject = appstruct['subject']
        to = config.ADMIN_EMAIL
        utils.send_mail(to=to, subject=subject, body=body)
    return {
        'appstruct': appstruct,
        'betacount': betacount,
        'form': form.render(),
        'followers': followers,
        'fortune': fortune,
        'freeslot_org': freeslot_org,
#        'freeslot_package': freeslot_package,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
#        'package': freeslot_package,
        'permissions': permissions,
        'slots_package': slots_package,
        'slotnum_org': slotnum_org,
        'slotnum_org_stripe': slotnum_org_stripe,
        'slotnum_package': slotnum_package,
        'slotnum_package_stripe': slotnum_package_stripe,
        'slots_org': slots_org,
        'slots_package': slots_package,
        'submitted': submitted,
        'userid': userid,
    }


def dashboard(request):
    """
        Present sidebar menus and released packages to user
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    # "Newer style" response. First initialize
    # default, then populate values we want.
    # Don't check keys, we know they exist.
    flash = request.session.pop_flash()
    if len(flash) > 0:
        flash = flash[0]
    betacount = utils.get_beta_count()
    colors = trove.colors
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    permissions = utils.get_permission_map(request=request)
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    avatar = utils.get_avatar(userid)
    freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe = \
        utils.get_slot_info(userid)
    # Get saved org from db
    freeslot_org = utils.get_org_selected(userid)
    recent_entries = utils.get_stats(criteria='dashboard', user=userid)
    timestamp_msg = "Released"
    response['avatar'] = avatar
    response['betacount'] = betacount
    response['colors'] = colors
    response['flash'] = flash
    response['followers'] = followers
    response['fortune'] = fortune
    response['freeslot_org'] = freeslot_org
#    response['freeslot_package'] = freeslot_package
    response['menu'] = menu
    response['num_downloads'] = num_downloads
    response['num_packages'] = num_packages
    response['num_packages_pypi'] = num_packages_pypi
    response['num_times_featured'] = num_times_featured
    response['num_downloads'] = num_downloads
#    response['package'] = freeslot_package
    response['permissions'] = permissions
    response['recent_entries'] = recent_entries
    response['slotnum_org'] = slotnum_org
    response['slotnum_org_stripe'] = slotnum_org_stripe
    response['slotnum_package'] = slotnum_package
    response['slotnum_package_stripe'] = slotnum_package_stripe
    response['slots_org'] = slots_org
    response['slots_package'] = slots_package
    response['timestamp_msg'] = timestamp_msg
    response['userid'] = userid
    return response


def github(request):
    """
        Process github service requests in order to automatically release
        packages to PyPI.
    """
    action = config.MANAGE_PACKAGE_ACTIONS[2]  # Tag and Release
    commits = github_token = org = orgset = None
    payload = repository = userid = None
    results = Response()  # Return nothing

    # Check commit message
    thundercats_are_goooooooooo = False  # Juno
    if 'payload' in request.POST:
        payload = json.loads(request.POST['payload'])
    if 'commits' in payload:
        commits = payload['commits']
        for commit in range(len(commits)):
            if 'message' in commits[commit]:
                message = commits[commit]['message']
                if message.startswith('Release'):
                    thundercats_are_goooooooooo = True
    if not thundercats_are_goooooooooo:
        # Punt
        return results

    # Get variables we need: owner, repository, userid, org
    if 'repository' in payload:
        repository = payload['repository']
        if 'owner' in repository:
            if 'name' in payload['repository']['owner']:
                owner = payload['repository']['owner']['name']
        if 'name' in repository:
            repository = repository['name']
    if 'pusher' in payload:
        if 'name' in payload['pusher']:
            userid = payload['pusher']['name']
    if userid != owner:  # Inject orgid as needed
        org = owner

    # Make sure oauth dance has occured else return
    if not utils.db.exists(config.REDIS_KEY_USER_GITHUB_OAUTH_TOKEN % userid):
        return results  # Punt
    else:  # Get GitHub token
        github_token = utils.db.get(config.REDIS_KEY_USER_GITHUB_OAUTH_TOKEN %
            userid)
    if not utils.db.exists(config.REDIS_KEY_USER_PYPI_OAUTH_TOKEN % userid):
        return results  # Punt
    if not utils.db.exists(config.REDIS_KEY_USER_PYPI_OAUTH_SECRET % userid):
        return results  # Punt

    # We have their token, now get their selected packages
    packages_selected = list()
    slots = utils.db.hgetall(config.REDIS_KEY_USER_PACKAGES_SELECTED % userid)
    for slot in slots.keys():
        orgset = json.loads(slots[slot])[1]
        package = json.loads(slots[slot])[0]
        packages_selected.append(package)

    # Look for a match and upload if found
    if repository in packages_selected:  # Match repo
        slots_org = utils.get_orgs_selected(userid)
        for item in slots_org.items():
            if org == item[1]:  # Match org
                orgset = item[0]
        utils.release_package(orgset, repository, action, slots_org,
            github_token, userid)

    return results


# Marketing FTW
def home_of_the_one_click_release(request):
    """
        Redirect inbound marketing link to /about
    """
    return HTTPFound(location='/about')


def login(request):
    """
        Do OAUTH dance with GitHub (for sign in) and PyPI (for releasing
        packages)
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    betacount = utils.get_beta_count()
    code = None
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    userid = authenticated_userid(request)
    qs = utils.get_query_string(request)
    qs = urlparse.parse_qs(qs)
    # PyPI OAuth, not used for login
    if 'oauth_token' in qs:
        auth = requests.auth.OAuth1(config.PYPI_OAUTH_CONSUMER_KEY,
            config.PYPI_OAUTH_CONSUMER_SECRET,
            unicode(utils.db.get(config.REDIS_KEY_USER_PYPI_OAUTH_TOKEN %
                userid)),
            unicode(utils.db.get(config.REDIS_KEY_USER_PYPI_OAUTH_SECRET %
                userid)),
            signature_type='auth_header')
        response = requests.get(config.PYPI_URL_OAUTH_ACCESS_TOKEN, auth=auth,
            verify=False)
        response = urlparse.parse_qs(response.content)
        utils.db.set(config.REDIS_KEY_USER_PYPI_OAUTH_SECRET % userid,
            unicode(response['oauth_token_secret'][0]))
        utils.db.set(config.REDIS_KEY_USER_PYPI_OAUTH_TOKEN % userid,
            unicode(response['oauth_token'][0]))
        return HTTPFound(location="/manage/account/pypi")
    if userid is not None:
        return HTTPFound(location="/dashboard")
    else:
        menu = utils.no_sign_in()
    headers = None
    userinfo = None
    if 'code' in qs:
        code = qs['code']
        token = utils.get_access_token(code)
        userinfo = utils.get_user_info(token)
        userinfo = json.loads(userinfo)
        avatar, email, name, userid = utils.get_user_id(userinfo)
        utils.set_avatar(userid, avatar)
        utils.set_email(userid, email)
        utils.set_name(userid, name)
        if not utils.db.exists(config.REDIS_KEY_USER_PLAN % userid):
            utils.set_plan(userid, 'free')
        utils.set_token(userid, token)
        utils.set_slots(userid)
        headers = remember(request, userid)
        utils.set_logged_in(userid)
        return HTTPFound(location="/dashboard", headers=headers)
    recent_users = dict()
    return {
        'betacount': betacount,
        'followers': followers,
        'fortune': fortune,
        'github_auth': config.GITHUB_URL_AUTH,
        'menu': menu,
        'headers': headers,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
        'recent_users': recent_users,
        'userid': userid,
    }


def logout(request):
    """
        Forget user
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    userid = authenticated_userid(request)
    headers = forget(request)
    utils.logged_out(userid)
    return HTTPFound(location="/", headers=headers)


# Do this when someone requests /manage/account/github
def manage_account_github(request):
    """
        Store username and password from the request in
        encrypted session cookie
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    betacount = utils.get_beta_count()
    data = list()
    flash = request.session.pop_flash()
    if len(flash) > 0:
        flash = flash[0]
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    permissions = utils.get_permission_map(request=request)
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    username = None
    password = None
    submit = False
    freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe = \
        utils.get_slot_info(userid)
    if 'submit' in request.POST:
        username = request.POST['username']
        password = request.POST['password']
        cookieval = {'username': username, 'password': password}
        request.session[config.COOKIE_GITHUB] = cookieval
        submit = True
    if config.COOKIE_GITHUB in request.session:
        data = request.session[config.COOKIE_GITHUB]
    if 'username' in data:
        username = data['username']
    if 'password' in data:
        password = data['password']
    if 'clear' in request.POST:
        del request.session[config.COOKIE_GITHUB]
        username = None
        password = None
    return {
        'betacount': betacount,
        'flash': flash,
        'followers': followers,
        'fortune': fortune,
        'freeslot_org': freeslot_org,
#        'freeslot_package': freeslot_package,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
#        'package': freeslot_package,
        'password': password,
        'permissions': permissions,
        'slotnum_org': slotnum_org,
        'slotnum_org_stripe': slotnum_org_stripe,
        'slotnum_package': slotnum_package,
        'slotnum_package_stripe': slotnum_package_stripe,
        'slots_org': slots_org,
        'slots_package': slots_package,
        'submit': submit,
        'userid': userid,
        'username': username,
    }


# Do this when someone requests /manage/account/pypi
def manage_account_pypi(request):
    """
        Store username and password from the request in
        encrypted session cookie
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    betacount = utils.get_beta_count()
    data = list()
    flash = request.session.pop_flash()
    if len(flash) > 0:
        flash = flash[0]
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    permissions = utils.get_permission_map(request=request)
    pypi_oauth_secret = None
    pypi_oauth_token = None
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    username = None
    password = None
    submit = False
    freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe = \
        utils.get_slot_info(userid)
    # Get saved orgs from db
    freeslot_org = utils.get_org_selected(userid)
    if 'pypi_oauth' in request.POST:
        # H/T Richard Jones
        auth = requests.auth.OAuth1(config.PYPI_OAUTH_CONSUMER_KEY,
            config.PYPI_OAUTH_CONSUMER_SECRET, signature_type='auth_header')
        response = requests.get(config.PYPI_URL_OAUTH_REQUEST_TOKEN, auth=auth,
            verify=False)
        qs = urlparse.parse_qs(response.content)
        if 'oauth_token_secret' in qs:
            pypi_oauth_secret = unicode(qs['oauth_token_secret'][0])
        if 'oauth_token' in qs:
            pypi_oauth_token = unicode(qs['oauth_token'][0])
        utils.db.set(config.REDIS_KEY_USER_PYPI_OAUTH_SECRET % userid,
            pypi_oauth_secret)
        utils.db.set(config.REDIS_KEY_USER_PYPI_OAUTH_TOKEN % userid,
            pypi_oauth_token)
        return HTTPFound(location=config.PYPI_URL_OAUTH_AUTHORIZE % (
            pypi_oauth_token, config.PYPI_URL_OAUTH_CALLBACK))
    if 'submit' in request.POST:
        username = request.POST['username']
        password = request.POST['password']
        cookieval = {'username': username, 'password': password}
        request.session[config.COOKIE_PYPI] = cookieval
        submit = True
    if config.COOKIE_PYPI in request.session:
        data = request.session[config.COOKIE_PYPI]
    if 'username' in data:
        username = data['username']
    if 'password' in data:
        password = data['password']
    if 'clear' in request.POST:
        utils.db.delete(config.REDIS_KEY_USER_PYPI_OAUTH_SECRET % userid)
        utils.db.delete(config.REDIS_KEY_USER_PYPI_OAUTH_TOKEN % userid)
    pypi_oauth_test = utils.pypi_oauth_test(userid)
    return {
        'betacount': betacount,
        'flash': flash,
        'followers': followers,
        'fortune': fortune,
        'freeslot_org': freeslot_org,
#        'freeslot_package': freeslot_package,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
#        'package': freeslot_package,
        'password': password,
        'permissions': permissions,
        'pypi_oauth_test': pypi_oauth_test,
        'slotnum_org': slotnum_org,
        'slotnum_org_stripe': slotnum_org_stripe,
        'slotnum_package': slotnum_package,
        'slotnum_package_stripe': slotnum_package_stripe,
        'slots_org': slots_org,
        'slots_package': slots_package,
        'submit': submit,
        'userid': userid,
        'username': username,
    }


def manage_billing(request):
    """
        Do stripe dance for payments
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    _display_cc = False
    # New style _userid
    _userid = authenticated_userid(request)
    appstruct = dict()
    betacount = utils.get_beta_count()
    choices = config.PLANS_CHOICES
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe = \
        utils.get_slot_info(_userid)
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    permissions = utils.get_permission_map(request=request)
    # Put plans in form
    plans = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.RadioChoiceWidget(values=choices),
        validator=colander.OneOf([choice[0] for choice in choices]),
        name='plan',
    )
    schema = colander.SchemaNode(colander.Mapping())
    schema.add(plans)
    stripe.api_key = config.STRIPE_API_KEY
    if _userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(_userid)
    qs = utils.get_query_string(request)
    qs = urlparse.parse_qs(qs)
    plan = None
    if 'plan' in qs:
        plan = qs['plan']
        if len(plan) > 0:
            plan = plan[0]
    if plan != 'free':
        if not utils.db.exists(config.REDIS_KEY_USER_CUSTOMER % _userid):
            _display_cc = True
    form = deform.Form(schema, buttons=('select',))
    # The user selected a plan
    if 'select' in request.POST:
        controls = request.POST.items()  # get the form controls
        try:
            appstruct = form.validate(controls)  # call validate
        except deform.ValidationFailure, e:  # catch the exception
            response['form'] = e.render(appstruct=appstruct)
            return response
        # the form submission succeeded, we have the data
        if 'plan' in appstruct:
            plan_selected = appstruct['plan']
            if utils.db.exists(config.REDIS_KEY_USER_CUSTOMER % _userid):
                # User selected free plan
                if plan_selected == 'free':
                # Cancel current plan if it exists
                    customer = json.loads(utils.db.get(
                        config.REDIS_KEY_USER_CUSTOMER % _userid))
                    if 'id' in customer:
                        cid = customer['id']
                        try:
                            customer = stripe.Customer.retrieve(cid)
                            customer.cancel_subscription()
                        except:
                            # stripe error
                            typ, out, tb = sys.exc_info()
                        utils.db.delete(config.REDIS_KEY_USER_CUSTOMER %
                            _userid)
                utils.config_slots(plan_selected, _userid)
                utils.set_plan(_userid, plan_selected)
                # Adjust current plan if it exists
                if utils.db.exists(config.REDIS_KEY_USER_CUSTOMER % _userid):
                    customer = json.loads(utils.db.get(
                        config.REDIS_KEY_USER_CUSTOMER % _userid))
                    if 'id' in customer:
                        cid = customer['id']
                        customer = stripe.Customer.retrieve(cid)
                        customer.update_subscription(plan=plan_selected)
                        utils.config_slots(plan_selected, _userid)
                        utils.set_plan(_userid, plan_selected)
                # Notify user
                request.session.flash("You selected the %s plan." %
                    plan_selected.capitalize())
                # Re-get slot info
                freeslot_org, freeslot_package, slotnum_org, \
                    slotnum_org_stripe, \
                    slots_org, slots_package, slotnum_package, \
                    slotnum_package_stripe = utils.get_slot_info(_userid)
            return HTTPFound(location='/manage/billing?plan=%s' %
                plan_selected)
    # The user submitted a payment form
    if 'plan' in request.POST and 'stripeToken' in request.POST:
        email = utils.get_email(_userid)
        plan_posted = request.POST['plan']
        token = request.POST['stripeToken']
        # Create a new customer
        try:
            customer = stripe.Customer.create(
                 card=token,
                 plan=plan_posted,
                 email=email,
            )
            utils.config_slots(plan_posted, _userid)
            utils.save_customer(customer, _userid)
            utils.set_plan(_userid, plan_posted)
            # Notify user
            request.session.flash("You selected the %s plan." %
                plan_posted.capitalize())
        except:
            typ, out, tb = sys.exc_info()
            request.session.flash("Sorry, something went wrong: %s" %
                out.message)
        # Re-get slot info
        freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
            slots_org, slots_package, slotnum_package, \
            slotnum_package_stripe = utils.get_slot_info(_userid)
    appstruct['plan'] = utils.get_plan(_userid)
    flash = request.session.pop_flash()
    if len(flash) > 0:
        flash = flash[0]
    response['betacount'] = betacount
    response['flash'] = flash
    response['followers'] = followers
    response['form'] = form.render(appstruct=appstruct)
    response['fortune'] = fortune
    response['freeslot_org'] = freeslot_org
#    response['freeslot_package'] = freeslot_package
    response['menu'] = menu
    response['num_downloads'] = num_downloads
    response['num_packages'] = num_packages
    response['num_packages_pypi'] = num_packages_pypi
    response['num_times_featured'] = num_times_featured
    response['plans_choices'] = config.PLANS_CHOICES
    response['plans_data'] = config.PLANS_DATA
    response['plan'] = plan
    response['permissions'] = permissions
    response['display_cc'] = _display_cc
    response['slotnum_org'] = slotnum_org
    response['slotnum_org_stripe'] = slotnum_org_stripe
    response['slotnum_package'] = slotnum_package
    response['slotnum_package_stripe'] = slotnum_package_stripe
    response['slots_org'] = slots_org
    response['slots_package'] = slots_package
    response['userid'] = _userid
    return response


# Do this when someone requests /manage/github-orgs
def manage_github_orgs(request):
    """
        Allow user to select/unselect orgs
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    flash = request.session.pop_flash()
    if len(flash) > 0:
        flash = flash[0]
    # stats
    betacount = utils.get_beta_count()
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    permissions = utils.get_permission_map(request=request)
    qs = utils.get_query_string(request)
    qs = urlparse.parse_qs(qs)
    slot = None
    if 'slot' in qs:
        slot = qs['slot']
        if len(slot) > 0:
            slot = int(slot[0])
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    token = utils.get_user_token(userid)
    freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe = \
        utils.get_slot_info(userid)
    # Get orgs and put in form
    user_orgs = json.loads(utils.get_user_orgs(token))
    choices = list()
    if not 'message' in user_orgs:  # No gh error, ok to proceed
        choices = utils.colanderize(choices,
            [org['login'] for org in user_orgs])
    choices.sort()
    orgs = colander.SchemaNode(
        colander.String(),
        missing=None,  # Need to be able to submit without selecting
        widget=deform.widget.RadioChoiceWidget(values=choices),
        validator=colander.OneOf([choice[0] for choice in choices]),
        name='organization',
        )
    schema = colander.SchemaNode(colander.Mapping())
    schema.add(orgs)
    # Retrieve current org, package from db
    org_selected = utils.get_org_selected(userid, slotget=slot)
    package = utils.get_package_selected(userid)
    appstruct = dict()
    appstruct['organization'] = org_selected
    # Config form buttons
    if org_selected:
        form = deform.Form(schema, buttons=('select', 'unselect'))
    else:
        if slot >= 0:
            form = deform.Form(schema, buttons=('select', 'remove slot'))
        else:  # Free slot cannot be removed
            form = deform.Form(schema, buttons=('select', ))
    # Do work
    if 'unselect' in request.POST:  # detect that the submit button was clicked
        controls = request.POST.items()  # get the form controls
        try:
            appstruct = form.validate(controls)  # call validate
        except deform.ValidationFailure, e:  # catch the exception
            return {
                'betacount': betacount,
                'flash': flash,
                'form': e.render(appstruct=appstruct),
                'followers': followers,
                'fortune': fortune,
                'freeslot_org': freeslot_org,
#                'freeslot_package': freeslot_package,
                'menu': menu,
                'num_downloads': num_downloads,
                'num_packages': num_packages,
                'num_packages_pypi': num_packages_pypi,
                'num_times_featured': num_times_featured,
                'package': package,
                'permissions': permissions,
                'slot': slot,
                'slotnum_org': slotnum_org,
                'slotnum_org_stripe': slotnum_org_stripe,
                'slotnum_package': slotnum_package,
                'slotnum_package_stripe': slotnum_package_stripe,
                'slots_org': slots_org,
                'slots_package': slots_package,
                'userid': userid,
            }
        # the form submission succeeded, we have the data
        utils.get_org_selected(userid, remove=True, slotdel=slot)
        return HTTPFound(location="/manage/github-orgs?slot=%s" % slot)
    if 'remove_slot' in request.POST:
        utils.remove_slot(slot, slots_org, userid, org=True)
        if slot > 0:
            slot = slot - 1
            return HTTPFound(location="/manage/github-orgs?slot=%s" % slot)
        else:
            return HTTPFound(location="/manage/github-orgs")
    if 'select' in request.POST:  # detect that the submit button was clicked
        controls = request.POST.items()  # get the form controls
        try:
            appstruct = form.validate(controls)  # call validate
        except deform.ValidationFailure, e:  # catch the exception
            return {
                'betacount': betacount,
                'flash': flash,
                'form': e.render(appstruct=appstruct),
                'followers': followers,
                'fortune': fortune,
                'freeslot_org': freeslot_org,
#                'freeslot_package': freeslot_package,
                'menu': menu,
                'num_downloads': num_downloads,
                'num_packages': num_packages,
                'num_packages_pypi': num_packages_pypi,
                'num_times_featured': num_times_featured,
                'package': package,
                'slot': slot,
                'slotnum_org': slotnum_org,
                'slotnum_org_stripe': slotnum_org_stripe,
                'slotnum_package': slotnum_package,
                'slotnum_package_stripe': slotnum_package_stripe,
                'slots_org': slots_org,
                'slots_package': slots_package,
                'permissions': permissions,
                'userid': userid,
            }
        # the form submission succeeded, we have the data
        # Save
        if 'organization' in appstruct:
            org = appstruct['organization']
        utils.get_org_selected(userid, org=org, slotset=slot)
        # Update slots
        freeslot_org = utils.get_org_selected(userid)
        slots_org = utils.get_orgs_selected(userid)
        request.session.flash('You selected %s' % org)
        # Redo flash
        flash = request.session.pop_flash()
        if len(flash) > 0:
            flash = flash[0]
    return {
        'betacount': betacount,
        'flash': flash,
        'form': form.render(appstruct=appstruct),
        'followers': followers,
        'fortune': fortune,
        'freeslot_org': freeslot_org,
#        'freeslot_package': freeslot_package,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
        'package': package,
        'permissions': permissions,
        'slot': slot,
        'slotnum_org': slotnum_org,
        'slotnum_org_stripe': slotnum_org_stripe,
        'slotnum_package': slotnum_package,
        'slotnum_package_stripe': slotnum_package_stripe,
        'slots_org': slots_org,
        'slots_package': slots_package,
        'userid': userid,
    }


def manage_github_orgs_add(request):
    """
        Add an organization slot if the plan allows
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    userid = authenticated_userid(request)
    slotnum_org = utils.db.get(config.REDIS_KEY_USER_SLOTNUM_ORG % userid)
    if slotnum_org:
        slotnum_org = int(slotnum_org)
    else:
        slotnum_org = 0
    _stripe_slotnum_org, _stripe_slotnum_package = utils.get_slots(userid)
    if _stripe_slotnum_org is not None:
        MAX = int(_stripe_slotnum_org)
    else:
        MAX = config.USER_SLOTMAX_ORG
    if not slotnum_org < MAX:
        request.session.flash('Sorry, your current plan does not allow that')
        return HTTPFound(location="/dashboard")
    utils.db.incr(config.REDIS_KEY_USER_SLOTNUM_ORG % userid)
#    slotnum_org = slotnum_org - 1
    return HTTPFound(location="/manage/github-orgs?slot=%s" % slotnum_org)


def manage_github_orgs_clear(request):
    """
        Clear all slots and orgs
    """
    userid = authenticated_userid(request)
    if userid:
        utils.db.delete(config.REDIS_KEY_USER_SLOTNUM_ORG % userid)
#        utils.db.delete(config.REDIS_KEY_USER_SLOTMAX_ORG % userid)
        utils.db.delete(config.REDIS_KEY_USER_ORGS_SELECTED % userid)
    return HTTPFound(location="/dashboard")


def manage_mail(request):
    """
        Provide form for message entry and send mail to beta
        users
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    appstruct = None
    betacount = utils.get_beta_count()
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    mail = Mail()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    permissions = utils.get_permission_map(request=request)
    submitted = False
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe = \
        utils.get_slot_info(userid)
    # Send mail
    form = deform.Form(mail, buttons=('Send', 'Test'))
    if 'Send' in request.POST:  # detect that the submit button was clicked
        controls = request.POST.items()  # get the form controls
        try:
            appstruct = form.validate(controls)  # call validate
        except deform.ValidationFailure, e:  # catch the exception
            return {
                'appstruct': appstruct,
                'betacount': betacount,
                'form': e.render(),
                'followers': followers,
                'fortune': fortune,
                'freeslot_org': freeslot_org,
#                'freeslot_package': freeslot_package,
                'menu': menu,
                'num_downloads': num_downloads,
                'num_packages': num_packages,
                'num_packages_pypi': num_packages_pypi,
                'num_times_featured': num_times_featured,
#                'package': freeslot_package,
                'permissions': permissions,
                'slotnum_org': slotnum_org,
                'slotnum_org_stripe': slotnum_org_stripe,
                'slotnum_package': slotnum_package,
                'slotnum_package_stripe': slotnum_package_stripe,
                'slots_org': slots_org,
                'slots_package': slots_package,
                'submitted': submitted,
                'userid': userid,
            }  # re-render the form with an exception
        # the form submission succeeded, we have the data
        submitted = True
        subject = appstruct['subject']
        count = 0
        for user in utils.db.smembers('beta_users'):
            to = utils.db.hget(user, 'email_address')
            full_name = utils.db.hget(user, 'full_name')
            if full_name is not None:
                full_name = full_name.decode('utf-8')
            body = config.MESSAGE % (full_name, appstruct['body'])
            utils.send_mail(to=to, subject=subject, body=body)
            count += 1
    if 'Test' in request.POST:
        controls = request.POST.items()  # get the form controls
        try:
            appstruct = form.validate(controls)  # call validate
        except deform.ValidationFailure, e:  # catch the exception
            return {
                'appstruct': appstruct,
                'betacount': betacount,
                'form': e.render(),
                'followers': followers,
                'fortune': fortune,
                'freeslot_org': freeslot_org,
#                'freeslot_package': freeslot_package,
                'menu': menu,
                'num_downloads': num_downloads,
                'num_packages': num_packages,
                'num_packages_pypi': num_packages_pypi,
                'num_times_featured': num_times_featured,
#                'package': freeslot_package,
                'permissions': permissions,
                'slotnum_org': slotnum_org,
                'slotnum_org_stripe': slotnum_org_stripe,
                'slotnum_package': slotnum_package,
                'slotnum_package_stripe': slotnum_package_stripe,
                'slots_org': slots_org,
                'slots_package': slots_package,
                'submitted': submitted,
                'userid': userid,
            }  # re-render the form with an exception
        # the form submission succeeded, we have the data
        submitted = True
        body = appstruct['body']
        subject = appstruct['subject']
        to = config.ADMIN_EMAIL
        utils.send_mail(to=to, subject=subject, body=body)
    return {
        'appstruct': appstruct,
        'betacount': betacount,
        'form': form.render(),
        'followers': followers,
        'fortune': fortune,
        'freeslot_org': freeslot_org,
#        'freeslot_package': freeslot_package,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
#        'package': freeslot_package,
        'permissions': permissions,
        'slots_package': slots_package,
        'slotnum_org': slotnum_org,
        'slotnum_org_stripe': slotnum_org_stripe,
        'slotnum_package': slotnum_package,
        'slotnum_package_stripe': slotnum_package_stripe,
        'slots_org': slots_org,
        'slots_package': slots_package,
        'submitted': submitted,
        'userid': userid,
    }


# Do this when someone requests /manage/package
def manage_package(request):
    """
        Process actions from request to select/unselect,
        test install, test release, and release package.
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    # Setup
    flash = request.session.pop_flash()
    if len(flash) > 0:
        flash = flash[0]
    qs = utils.get_query_string(request)
    qs = urlparse.parse_qs(qs)
    betacount = utils.get_beta_count()
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    permissions = utils.get_permission_map(request=request)
    err = myform = orgset = package = str()
    num_repos = slot = 0
    page = 1
    submitted = False
    tree = url = None
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    if not utils.check_email(userid):
        return HTTPFound('/signup')
    # Check for selected package
    if 'slot' in qs:
        slot = qs['slot']
        if len(slot) > 0:
            slot = int(slot[0])
    package = utils.get_package_selected(userid, slotget=slot)
    if package is not None:
        package, orgset = json.loads(package)
    token = utils.get_user_token(userid)
    freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe = \
        utils.get_slot_info(userid)
    # Search
    search = None
    if 'search' in request.POST:
        search = request.POST['search']
    # Put repos in form
    org = None
    page = 0
    if 'org' in qs:
        org = qs['org']
        if len(org) > 0:
            org = int(org[0])
    if 'page' in qs:
        page = qs['page']
        if len(page) > 0:
            page = int(page[0])
    myform, num_repos = utils.put_repos_in_form(page, token, org,
        permissions, slots_org, slot, search=search, user=userid)
    # Remove selection
    if 'unselect-package' in request.POST:
        utils.get_package_selected(userid, remove=True, slotdel=slot)
        return HTTPFound(location="/manage/package?slot=%s" % slot)
    # Release selection and perform other actions
    action = None
    for mpa in config.MANAGE_PACKAGE_ACTIONS:
        if mpa in request.POST:
            action = mpa
    if action:
        submitted = True
        err = utils.release_package(orgset, package, action, slots_org,
            token, userid, ttw=True, slot=slot)
        if err == str():  # pypi_oauth_test failed
            request.session.flash('Please authorize this application on PyPI.')
            return HTTPFound(location="/manage/account/pypi")
        # Update slots
#        freeslot_package = utils.get_package_selected(userid)
        slots_package = utils.get_packages_selected(userid)
    # User is selecting a package
    appstruct = None
    if 'select' in request.POST:  # detect that the submit button was clicked
        controls = request.POST.items()  # get the form controls
        try:
            appstruct = myform.validate(controls)  # call validate
        except deform.ValidationFailure, e:  # catch the exception
            return {
                'appstruct': appstruct,
                'betacount': betacount,
                'error': err,
                'flash': flash,
                'form': e.render(),
                'followers': followers,
                'fortune': fortune,
                'freeslot_org': freeslot_org,
#                'freeslot_package': freeslot_package,
                'menu': menu,
                'num_downloads': num_downloads,
                'num_packages': num_packages,
                'num_packages_pypi': num_packages_pypi,
                'num_times_featured': num_times_featured,
                'num_repos': num_repos,
                'org': org,
                'page': page,
                'package': package,
                'permissions': permissions,
                'slot': slot,
                'slotnum_org': slotnum_org,
                'slotnum_org_stripe': slotnum_org_stripe,
                'slotnum_package': slotnum_package,
                'slotnum_package_stripe': slotnum_package_stripe,
                'slots_org': slots_org,
                'slots_package': slots_package,
                'submitted': submitted,
                'tree': tree,
                'url': url,
                'userid': userid,
            }  # re-render the form with an exception
        # the form submission succeeded, we have the data
        # Save
        package = utils.get_package_selected(userid, orgset=org,
            package=appstruct['repository'], slotset=slot)
        # Update slots
#        freeslot_package = utils.get_package_selected(userid)
        slots_package = utils.get_packages_selected(userid)
        if package is not None:
            # Inject orgid as needed
            if orgset is not None and org is not None:
                if str(org) in slots_org:
                    userid = slots_org[str(org)]
            commits = json.loads(utils.get_repo_commits(package, user=userid,
                token=token))
            last_commit = None
            if not 'message' in commits:  # No gh error, ok to proceed
                last_commit = commits[0]['sha']
            tree = json.loads(utils.get_repo_tree(package, key=last_commit,
                token=token, user=userid))
            url = '%s/%s/%s/tree/master' % (config.GITHUB_URL, userid, package)
#    # Remove repo
#    if 'remove_repository' in request.POST:
#        controls = request.POST.items()  # get the form controls
#        try:
#            appstruct = myform.validate(controls)  # call validate
#        except deform.ValidationFailure, e:  # catch the exception
#            response['form'] = e.render()
#            return response
#        if 'repository' in appstruct:
#            package = appstruct['repository']
#            # Inject orgid as needed
#            if orgset is not None and org is not None:
#                if str(org) in slots_org:
#                    userid = slots_org[str(org)]
#            utils.delete_repo(package, token, userid)
#            request.session.flash('Deleted %s' % package)
#            if org >= 0:
#                return HTTPFound(location="/manage/package?slot=%s&org=%s" %
#                    (slot, org))
#            else:
#                return HTTPFound(location="/manage/package?slot=%s" % slot)
    # Remove slot
    if 'remove_slot' in request.POST:
        if slot > 0:
            utils.remove_slot(slot, slots_package, userid)
            slot = slot - 1
        else:
            request.session.flash('Sorry, you cannot remove the free slot')
        if org >= 0:
            return HTTPFound(location="/manage/package?slot=%s&org=%s" %
                (slot, org))
        else:
            return HTTPFound(location="/manage/package?slot=%s" % slot)
    # User has selected a package and is not removing or releasing
    url = None
    if package:
        # Inject orgid as needed
        if orgset is not None:
            if str(orgset) in slots_org:
                userid = slots_org[str(orgset)]
        commits = json.loads(utils.get_repo_commits(package, user=userid,
            token=token))
        last_commit = None
        if not 'message' in commits:  # No gh error, ok to proceed
            last_commit = commits[0]['sha']
        tree = json.loads(utils.get_repo_tree(package, key=last_commit,
            token=token, user=userid))
        url = '%s/%s/%s/tree/master' % (config.GITHUB_URL, userid, package)
        return {
            'betacount': betacount,
            'error': err,
            'flash': flash,
            'form': None,
            'followers': followers,
            'fortune': fortune,
            'freeslot_org': freeslot_org,
#            'freeslot_package': freeslot_package,
            'menu': menu,
            'num_downloads': num_downloads,
            'num_packages': num_packages,
            'num_packages_pypi': num_packages_pypi,
            'num_repos': num_repos,
            'num_times_featured': num_times_featured,
            'org': org,
            'page': page,
            'slot': slot,
            'slotnum_org': slotnum_org,
            'slotnum_org_stripe': slotnum_org_stripe,
            'slotnum_package': slotnum_package,
            'slotnum_package_stripe': slotnum_package_stripe,
            'slots_org': slots_org,
            'slots_package': slots_package,
            'submitted': submitted,
            'package': package,
            'permissions': permissions,
            'tree': tree,
            'url': url,
            'userid': userid,
        }
    if submitted:
        form = None
    else:
        form = myform.render()
    return {
        'betacount': betacount,
        'error': err,
        'flash': flash,
        'form': form,
        'followers': followers,
        'fortune': fortune,
        'freeslot_org': freeslot_org,
#        'freeslot_package': freeslot_package,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
        'num_repos': num_repos,
        'org': org,
        'page': page,
        'package': package,
        'permissions': permissions,
        'slot': slot,
        'slotnum_org': slotnum_org,
        'slotnum_org_stripe': slotnum_org_stripe,
        'slotnum_package': slotnum_package,
        'slotnum_package_stripe': slotnum_package_stripe,
        'slots_org': slots_org,
        'slots_package': slots_package,
        'submitted': submitted,
        'tree': tree,
        'userid': userid,
    }


def manage_package_add(request):
    """
        Add package slot if the plan allows
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    userid = authenticated_userid(request)
    err, slotnum_package = utils.add_package_slot(userid)
    if err == 1:
        request.session.flash('Sorry, your current plan does not allow that')
        return HTTPFound(location="/dashboard")
    else:
        return HTTPFound(location="/manage/package?slot=%s" % slotnum_package)


def manage_package_bulk(request):
    """
        Add slots and packages en masse
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    appstruct = None
    betacount = utils.get_beta_count()
    bulk = Bulk()
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    permissions = utils.get_permission_map(request=request)
    results = str()
    submitted = False
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe = \
        utils.get_slot_info(userid)
    # Bulk add
    form = deform.Form(bulk, buttons=('Add', ))
    if 'Add' in request.POST:  # detect that the submit button was clicked
        controls = request.POST.items()  # get the form controls
        try:
            appstruct = form.validate(controls)  # call validate
        except deform.ValidationFailure, e:  # catch the exception
            return {
                'appstruct': appstruct,
                'betacount': betacount,
                'form': e.render(),
                'followers': followers,
                'fortune': fortune,
                'freeslot_org': freeslot_org,
#                'freeslot_package': freeslot_package,
                'menu': menu,
                'num_downloads': num_downloads,
                'num_packages': num_packages,
                'num_packages_pypi': num_packages_pypi,
                'num_times_featured': num_times_featured,
#                'package': freeslot_package,
                'permissions': permissions,
                'results': results,
                'slotnum_org': slotnum_org,
                'slotnum_org_stripe': slotnum_org_stripe,
                'slotnum_package': slotnum_package,
                'slotnum_package_stripe': slotnum_package_stripe,
                'slots_org': slots_org,
                'slots_package': slots_package,
                'submitted': submitted,
                'userid': userid,
            }  # re-render the form with an exception
        # the form submission succeeded, we have the data
        submitted = True
        packages = appstruct['packages']
        results = utils.bulk_add(packages, userid)
        freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
            slots_org, slots_package, slotnum_package, \
            slotnum_package_stripe = utils.get_slot_info(userid)
    return {
        'appstruct': appstruct,
        'betacount': betacount,
        'form': form.render(),
        'followers': followers,
        'fortune': fortune,
        'freeslot_org': freeslot_org,
#        'freeslot_package': freeslot_package,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
#        'package': freeslot_package,
        'permissions': permissions,
        'results': results,
        'slotnum_org': slotnum_org,
        'slotnum_org_stripe': slotnum_org_stripe,
        'slotnum_package': slotnum_package,
        'slotnum_package_stripe': slotnum_package_stripe,
        'slots_org': slots_org,
        'slots_package': slots_package,
        'submitted': submitted,
        'userid': userid,
    }


def manage_package_clear(request):
    """
        Clear all slots and packages
    """
    userid = authenticated_userid(request)
    if userid:
        utils.db.delete(config.REDIS_KEY_USER_SLOTNUM_PACKAGE % userid)
#        utils.db.delete(config.REDIS_KEY_USER_SLOTMAX_PACKAGE % userid)
        utils.db.delete(config.REDIS_KEY_USER_PACKAGES_SELECTED % userid)
    return HTTPFound(location="/dashboard")


# Do this when someone requests '/manage/package/new'
def manage_package_new(request):
    """
        Process name and paster template selection from form to
        create new package and save to GitHub
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    if not config.COOKIE_GITHUB in request.session:
        request.session.flash('Please enter your GitHub account credentials')
        return HTTPFound(location="/manage/account/github")
    appstruct = dict()
    betacount = utils.get_beta_count()
    error = False
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    permissions = utils.get_permission_map(request=request)
    org = None
    out = str()
    qs = utils.get_query_string(request)
    qs = urlparse.parse_qs(qs)
    submitted = False
    if 'org' in qs:
        org = qs['org']
        if len(org) > 0:
            org = org[0]
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    token = utils.get_user_token(userid)
    freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe = \
        utils.get_slot_info(userid)
    # Put templates in form
    choices = config.PASTER_TEMPLATE_CHOICES
    templates = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.RadioChoiceWidget(values=choices),
        validator=colander.OneOf([choice[0] for choice in choices]),
        name='template',
    )
    package_name = colander.SchemaNode(
        colander.String(),
        name='name',
        validator=utils.validate_package,
    )
    schema = colander.SchemaNode(colander.Mapping())
    schema.add(templates)
    schema.add(package_name)
    template = None
    if org:
        form = deform.Form(schema,
            action="/manage/package/new?org=%s" % org,
            buttons=('create',))
    else:
        form = deform.Form(schema, buttons=('create',))
    response['betacount'] = betacount
    response['followers'] = followers
    response['fortune'] = fortune
    response['menu'] = menu
    response['num_downloads'] = num_downloads
    response['num_packages'] = num_packages
    response['num_packages_pypi'] = num_packages_pypi
    response['num_times_featured'] = num_times_featured
    response['num_downloads'] = num_downloads
    response['userid'] = userid
    response['permissions'] = permissions
#    response['package'] = freeslot_package
    response['form'] = form.render()
    response['freeslot_org'] = freeslot_org
#    response['freeslot_package'] = freeslot_package
    response['org'] = org
    response['slotnum_org'] = slotnum_org
    response['slotnum_org_stripe'] = slotnum_org_stripe
    response['slotnum_package'] = slotnum_package
    response['slotnum_package_stripe'] = slotnum_package_stripe
    response['slots_org'] = slots_org
    response['slots_package'] = slots_package
    # Create package
    if 'name' in request.POST:
        controls = request.POST.items()  # get the form controls
        submitted = True
        try:
            appstruct = form.validate(controls)  # call validate
        except deform.ValidationFailure, e:  # catch the exception
            response['form'] = e.render()
            return response
        if 'template' in appstruct:
            template = appstruct['template']
        error, out = utils.create_package(request, slots_org, template,
            token, userid, org=org)
    response['error'] = error
    response['out'] = out.decode('utf-8')
    response['submitted'] = submitted
    return response


def manage_twitter(request):
    """
        Provide form for tweet entry and send tweet via Twitter API
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    appstruct = None
    betacount = utils.get_beta_count()
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    permissions = utils.get_permission_map(request=request)
    tweet = Tweet()
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe = \
        utils.get_slot_info(userid)
    submitted = False
    # Send tweet
    form = deform.Form(tweet, buttons=('Send',))
    if 'Send' in request.POST:  # detect that the submit button was clicked
        controls = request.POST.items()  # get the form controls
        try:
            appstruct = form.validate(controls)  # call validate
        except deform.ValidationFailure, e:  # catch the exception
            return {
                'appstruct': appstruct,
                'betacount': betacount,
                'form': e.render(),
                'followers': followers,
                'fortune': fortune,
                'freeslot_org': freeslot_org,
#                'freeslot_package': freeslot_package,
                'menu': menu,
                'num_downloads': num_downloads,
                'num_packages': num_packages,
                'num_packages_pypi': num_packages_pypi,
                'num_times_featured': num_times_featured,
#                'package': freeslot_package,
                'permissions': permissions,
                'slotnum_package': slotnum_package,
                'slots_package': slots_package,
                'submitted': submitted,
                'userid': userid,
            }  # re-render the form with an exception
        # the form submission succeeded, we have the data
        submitted = True
        tweet = appstruct['tweet']
        utils.send_tweet(tweet)
    return {
        'appstruct': appstruct,
        'betacount': betacount,
        'form': form.render(),
        'followers': followers,
        'fortune': fortune,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
#        'package': freeslot_package,
        'permissions': permissions,
        'freeslot_org': freeslot_org,
#        'freeslot_package': freeslot_package,
        'slotnum_org': slotnum_org,
        'slotnum_org_stripe': slotnum_org_stripe,
        'slotnum_package': slotnum_package,
        'slotnum_package_stripe': slotnum_package_stripe,
        'slots_org': slots_org,
        'slots_package': slots_package,
        'submitted': submitted,
        'userid': userid,
    }


# Marketing FTW
def one_click(request):
    """
        Redirect to /about
    """
    return HTTPFound(location='/about')


def plans(request):
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    permissions = utils.get_permission_map(request=request)
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe = \
        utils.get_slot_info(userid)
    # stats
    betacount = utils.get_beta_count()
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    response['betacount'] = betacount
    response['followers'] = followers
    response['fortune'] = fortune
    response['freeslot_org'] = freeslot_org
#    response['freeslot_package'] = freeslot_package
    response['menu'] = menu
    response['num_downloads'] = num_downloads
    response['num_packages'] = num_packages
    response['num_packages_pypi'] = num_packages_pypi
    response['num_times_featured'] = num_times_featured
    response['permissions'] = permissions
    response['slotnum_org'] = slotnum_org
    response['slotnum_org_stripe'] = slotnum_org_stripe
    response['slotnum_package'] = slotnum_package
    response['slotnum_package_stripe'] = slotnum_package_stripe
    response['slots_org'] = slots_org
    response['slots_package'] = slots_package
    response['userid'] = userid
    return response


def vanity_403(request):
    """
        Customize the pyramid 403 response
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    betacount = utils.get_beta_count()
    changelog = utils.get_stats(criteria='changelog')
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    most_downloads = utils.get_stats(criteria='downloaded')
    most_vain = utils.get_stats(criteria='featured')
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    releases = utils.get_stats(criteria='releases')
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    return {
        'betacount': betacount,
        'entries': changelog,
        'followers': followers,
        'fortune': fortune,
        'menu': menu,
        'most_downloads': most_downloads,
        'most_vain': most_vain,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
        'releases': releases,
        'userid': userid,
    }


def vanity_404(request):
    """
        Customize the pyramid 404 response
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    betacount = utils.get_beta_count()
    changelog = utils.get_stats(criteria='changelog')
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    most_downloads = utils.get_stats(criteria='downloaded')
    most_vain = utils.get_stats(criteria='featured')
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    return {
        'betacount': betacount,
        'entries': changelog,
        'followers': followers,
        'fortune': fortune,
        'menu': menu,
        'most_downloads': most_downloads,
        'most_vain': most_vain,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
        'userid': userid,
    }


# Do this when someone requests '/about'
def vanity_about(request):
    """
        The /about view, displays marketing mumbo jumbo.
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    betacount = utils.get_beta_count()
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    return {
        'betacount': betacount,
        'followers': followers,
        'fortune': fortune,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
        'userid': userid,
    }


def vanity_activity(request):  # Do this when someone requests '/activity'
    """
        The /activity view, displays recent activity from PyPI.
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    betacount = utils.get_beta_count()
    changelog = utils.get_stats(criteria='changelog')
    colors = trove.colors
    flash = request.session.pop_flash()
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    most_downloads = utils.get_stats(criteria='downloaded', limit=9)
    most_vain = utils.get_stats(criteria='featured', limit=9)
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    releases = utils.get_stats(criteria='releases')
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    return {
        'betacount': betacount,
        'colors': colors,
        'entries': changelog,
        'flash': flash,
        'followers': followers,
        'fortune': fortune,
        'most_downloads': most_downloads,
        'most_vain': most_vain,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
        'releases': releases,
        'userid': userid,
    }


# Redir /info
def vanity_info_package(request):  # redir
    """
        /package/<package> used to be /info/<package>
    """
    package = request.matchdict['package']
    return HTTPMovedPermanently(location='/package/%s' % package)


# Do this when someone requests '/package/<package>'
def vanity_package(request):
    """
        Display /package/<package> info.
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    betacount = utils.get_beta_count()
    changelog = utils.get_stats(criteria='changelog')
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    render_failed = False
    tab = None
    fortune = utils.get_fortune()
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    package = request.matchdict['package']
    qs = utils.get_query_string(request)
    if qs is not '':
        if qs.split('=')[0] == 'tab':  # yuck
            tab = qs.split('=')[1]  # yuck too
    if package != package.lower():
        package = package.lower()
        if tab is not None:
            return HTTPMovedPermanently(
                location="/package/%s?tab=%s" % (package, tab))
        else:
            return HTTPMovedPermanently(
                location="/package/%s" % package)
    docs = utils.check_docs(package)
    featured_by = utils.get_featured_by(package)
    files = utils.check_files(package)
    grids = utils.check_grids(package)
    package = utils.get_normalized_package(package)
    package_lower = package.lower()
    timestamp = utils.get_timestamp(package)
    version = utils.get_package_version(package)
    metadata = utils.get_package_metadata(package, version)
    if 'classifiers' in metadata:
        classifiers = metadata['classifiers']
    else:
        classifiers = list()
    num_classifiers = len(classifiers)
    python3_status = False
    if classifiers is not None:
        python3_status = utils.get_python3_status(classifiers)
    colors = trove.colors
    if 'description' in metadata:
        description = metadata['description']
    else:
        description = str()
    if 'summary' in metadata:
        summary = metadata['summary']
    else:
        summary = str()
    metadata = utils.check_metadata(metadata)  # sanitize
    try:
        description = publish_parts(description, writer_name='html',
            settings_overrides=config.DOCUTILS_SETTINGS)
        description = description['html_body']
    except:
        # Render failed
        render_failed = True
        description = '%s' % description
    downloads = utils.get_package_downloads(package)
    count = downloads
    downloads = utils.locale_format(int(downloads))
    package_quality, trash_report = utils.get_trash_report(package)
    score = utils.get_package_score(config.REDIS_KEY_PACKAGES_FEATURED,
        package)
    return {
        'betacount': betacount,
        'entries': changelog,
        'classifiers': classifiers,
        'count': count,
        'colors': colors,
        'description': description,
        'docs': docs,
        'downloads': downloads,
        'featured_by': featured_by,
        'followers': followers,
        'files': files,
        'fortune': fortune,
        'grids': grids,
        'menu': menu,
        'metadata': metadata,
        'num_classifiers': num_classifiers,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
        'package': package,
        'package_lower': package_lower,
        'package_quality': package_quality,
        'python3_status': python3_status,
        'render_failed': render_failed,
        'summary': summary,
        'timestamp': timestamp,
        'score': score,
        'trash_report': trash_report,
        'version': version,
        'userid': userid,
    }


def vanity_pypi_package(request):  # redir
    """
        /package/<package> used to be /pypi/<package>
    """
    package = request.matchdict['package']
    return HTTPMovedPermanently(location='/package/%s' % package)


def vanity_root(request):  # Do this when someone requests '/'
    """
        Display featured entries
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    betacount = utils.get_beta_count()
    colors = trove.colors
    discuss = False
    error = False
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    recent_entries = utils.get_stats(criteria='entries')
    qs = utils.get_query_string(request)
    tab = config.DEFAULT_TAB
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    if qs is not '':
        if qs.split('=')[0] == 'tab':  # yuck
            tab = qs.split('=')[1]  # yuck too
    # Redir from / to /package/<package>?tab=downloaded
    if 'package' in request.POST and userid:
        package = request.POST['package']
        if utils.check_input(package):
            utils.score_entry(
                utils.get_normalized_package(package), user=userid)
            if package != package.lower():
                package = package.lower()
                return HTTPMovedPermanently(  # redir
                        location="/package/%s?tab=%s" % (package, tab))
            else:
                return HTTPFound(
                        location="/package/%s?tab=%s" % (package, tab))
        else:
            error = True
    # Redir from /activity to /activity
    if 'package:activity' in request.POST and userid:
        package = request.POST['package:activity']
        if utils.check_input(package):
            utils.score_entry(
                utils.get_normalized_package(package), user=userid)
            request.session.flash(package)
            return HTTPFound(location="/activity")
        else:
            error = True
    if 'package:main' in request.POST and userid:
        package = request.POST['package:main']
        if utils.check_input(package):
            utils.score_entry(
                utils.get_normalized_package(package), user=userid)
            request.session.flash(package)
            return HTTPFound(location="/")
        else:
            error = True
    # Redir from /package/<package>?tab=info to
    # /package/<package>?tab=featured
    if 'package:info' in request.POST and userid:
        package = request.POST['package:info']
        tab = 'featured'
        if utils.check_input(package):
            utils.score_entry(
                utils.get_normalized_package(package), user=userid)
            if package != package.lower():
                package = package.lower()
                return HTTPMovedPermanently(  # redir
                        location="/package/%s?tab=%s" % (package, tab))
            else:
                return HTTPFound(
                        location="/package/%s?tab=%s" % (package, tab))
        else:
            error = True
    flash = request.session.pop_flash()
    timestamp_msg = "Last featured by"
    return {
        'betacount': betacount,
        'count': 0,
        'colors': colors,
        'discuss': discuss,
        'error': error,
        'flash': flash,
        'followers': followers,
        'fortune': fortune,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
        'recent_entries': recent_entries,
        'timestamp_msg': timestamp_msg,
        'userid': userid,
    }


# Do this when someone requests '/signup'
def vanity_signup(request):
    """
        Display and process sign up form.
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    _MSG = ("Welcome to pythonpackages.com! To get started, please read: "
        "http://docs.pythonpackages.com/en/latest/introduction.html. Also, "
        "please feel free to reply to this e-mail with any questions you "
        "may have about the service.")
    appstruct = dict()
    betacount = utils.get_beta_count()
    changelog = utils.get_stats(criteria='changelog')
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    colors = trove.colors
    most_downloads = utils.get_stats(criteria='downloaded')
    most_vain = utils.get_stats(criteria='featured')
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    recent_troves = dict()
    releases = utils.get_stats(criteria='releases')
    submitted = False
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    person = Person()
    form = deform.Form(person, buttons=('sign up',))
    if 'sign_up' in request.POST:  # detect that the submit button was clicked
        controls = request.POST.items()  # get the form controls
        try:
            appstruct = form.validate(controls)  # call validate
        except deform.ValidationFailure, e:  # catch the exception
            return {
                'appstruct': appstruct,
                'betacount': betacount,
                'changelog': changelog,
                'colors': colors,
                'form': e.render(),
                'followers': followers,
                'fortune': fortune,
                'menu': menu,
                'most_downloads': most_downloads,
                'most_vain': most_vain,
                'num_downloads': num_downloads,
                'num_packages': num_packages,
                'num_packages_pypi': num_packages_pypi,
                'num_times_featured': num_times_featured,
                'recent_troves': recent_troves,
                'releases': releases,
                'submitted': submitted,
                'userid': userid,
            }  # re-render the form with an exception
        # the form submission succeeded, we have the data
        submitted = True
        first_name = appstruct['first_name']
        last_name = appstruct['last_name']
        email_address = appstruct['email_address']
        github_username = appstruct['github_username']
        trove_classifiers = appstruct['classifiers']
        full_name = '%s %s' % (first_name, last_name)
        utils.set_email(github_username, email_address)
        utils.set_name(github_username, full_name)
        for trove_classifier in trove_classifiers:
            utils.db.incr(config.REDIS_KEY_TROVE_CLASSIFIER % trove_classifier)
            utils.db.lpush(config.REDIS_KEY_TROVE_CLASSIFIERS_ENTERED,
                utils.trove_lookup(trove_classifier))
            try:
                utils.db.zadd(
                    config.REDIS_KEY_TROVE_CLASSIFIERS_FEATURED,
                    utils.db.get(config.REDIS_KEY_TROVE_CLASSIFIER %
                        trove_classifier),
                    utils.trove_lookup(trove_classifier),
                )
            except:
                utils.db.zadd(
                    config.REDIS_KEY_TROVE_CLASSIFIERS_FEATURED,
                    utils.trove_lookup(trove_classifier),
                    utils.db.get(config.REDIS_KEY_TROVE_CLASSIFIER %
                        trove_classifier),
                )
        full_name = '%s %s' % (first_name, last_name)
        first_name = first_name.lower()
        last_name = last_name.lower()
        utils.db.hset(config.REDIS_KEY_BETA_USER % (last_name, first_name),
            'full_name', full_name)
        utils.db.hset(config.REDIS_KEY_BETA_USER % (last_name, first_name),
            'email_address', email_address)
        utils.db.hset(config.REDIS_KEY_BETA_USER % (last_name, first_name),
            'github_username', github_username)
        utils.db.hset(config.REDIS_KEY_BETA_USER % (last_name, first_name),
            'trove_classifiers', trove_classifiers)
        utils.db.sadd(config.REDIS_KEY_BETA_USERS, config.REDIS_KEY_BETA_USER
            % (last_name, first_name))
        utils.db.sadd(config.REDIS_KEY_USERS_WHITELIST, github_username)
        body = pprint.pformat(appstruct)
        utils.send_mail(to=None, subject='New sign up', body=body)
        utils.send_mail(to=email_address,
            subject='Welcome to pythonpackages.com!',
            body=config.MESSAGE % (full_name, _MSG))
    form = form.render()
    return {
        'appstruct': appstruct,
        'betacount': betacount,
        'changelog': changelog,
        'colors': trove.colors,
        'form': form,
        'followers': followers,
        'fortune': fortune,
        'menu': menu,
        'most_downloads': most_downloads,
        'most_vain': most_vain,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
        'recent_troves': recent_troves,
        'submitted': submitted,
        'userid': userid,
    }


# Do this when someone requests '/user/<user>'
def vanity_user(request):
    """
        Display per user info.
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    avatar = None
    betacount = utils.get_beta_count()
    colors = trove.colors
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    package = None
    user = request.matchdict['user']
    userid = authenticated_userid(request)
    avatar = utils.get_avatar(user)
    if not utils.is_site_user(user):
        return HTTPNotFound()
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    if user == userid:  # i am me
        permissions = utils.get_permission_map(request=request)
        package = utils.get_package_selected(userid)
    else:  # we are not us, so perms are irrelevant
        permissions = utils.get_permission_map()
    try:  # XXX Requires db
        recent_entries = utils.get_stats(criteria='user', limit=5, user=user)
    except:
        recent_entries = list()
    timestamp_msg = "Last featured by"
    return {
        'avatar': avatar,
        'betacount': betacount,
        'colors': colors,
        'followers': followers,
        'fortune': fortune,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
        'package': package,
        'permissions': permissions,
        'recent_entries': recent_entries,
        'timestamp_msg': timestamp_msg,
        'userid': userid,
        'user': user,
    }


# Do this when someone requests '/users'
def vanity_users(request):
    """
        Display recent users that have featured packages.
    """
#    # Redir https
#    if request.headers.get('X-Forwarded-Proto') is not None:
#        if request.headers['X-Forwarded-Proto'] != 'https':
#            return HTTPMovedPermanently(location="https://%s%s" % (
#                request.host, request.path_qs))
    # Check db
    response = utils.get_response()
    try:
        utils.db.ping()
    except:
        return response
    betacount = utils.get_beta_count()
    discuss = False
    followers = utils.get_followers()
    fortune = utils.get_fortune()
    num_downloads, num_packages, num_packages_pypi, num_times_featured = \
        utils.get_numbers()
    fortune = utils.get_fortune()
    userid = authenticated_userid(request)
    if userid is None:
        menu = utils.no_sign_in()
    else:
        menu = utils.get_menu(userid)
    logged_in = utils.get_logged_in()
    recent_users = utils.get_stats(criteria='users')
    user_list = utils.get_stats(criteria='user_list')
    return {
        'betacount': betacount,
        'discuss': discuss,
        'followers': followers,
        'fortune': fortune,
        'logged_in': logged_in,
        'menu': menu,
        'num_downloads': num_downloads,
        'num_packages': num_packages,
        'num_packages_pypi': num_packages_pypi,
        'num_times_featured': num_times_featured,
        'recent_users': recent_users,
        'userid': userid,
        'user_list': user_list,
    }
