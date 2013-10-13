# encoding: utf-8
from beaker.cache import cache_region
from collections import OrderedDict
from email.mime.text import MIMEText
from pypi.trashfinder.cli import process_package
from pyramid.security import has_permission
from yolk.pypi import CheeseShop
from . import config
from . import mkcfg as d2
from . import trove
import ConfigParser
import colander
import datetime
import deform
import fortune
import json
import locale
import logging
import os
import pbs
import re
import redis
import requests
import sys
import urllib
import urlparse
import vanity
import shutil
import smtplib
import tempfile
import twitter as Twitter
import xmlrpclib


if 'REDISTOGO_URL' in os.environ:
    urlparse.uses_netloc.append('redis')
    url = urlparse.urlparse(os.environ['REDISTOGO_URL'])
    db = redis.Redis(host=url.hostname, port=url.port, db=0,
        password=url.password)
else:
    db = redis.StrictRedis(host='localhost', port=6379, db=0)
fortune.make_fortune_data_file(config.FORTUNE_FILE)
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
pypi = xmlrpclib.ServerProxy(config.PYPI_URL)
yolk = CheeseShop()
twitter = Twitter.Api(consumer_key=config.TWITTER_CONSUMER_KEY,
    consumer_secret=config.TWITTER_CONSUMER_SECRET,
    access_token_key=config.TWITTER_ACCESS_TOKEN,
    access_token_secret=config.TWITTER_ACCESS_SECRET)
valid_package = re.compile('\A\w+\Z|\A\w+\.\w+\Z|\A\w+\.\w+\.\w+\Z')


def get_logger():
    """
        Do logging dance
    """
    # log levels: debug, info, warn, error, critical
    logger = logging.getLogger("pythonpackages.com")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = get_logger()


#def add_package_slot(user, here=None):
def add_package_slot(user):
    """
        Add package slot. Optionally accept `here` to add slot
        above current slot.
    """
    err = 0
    slotnum_package = db.get(config.REDIS_KEY_USER_SLOTNUM_PACKAGE %
        user)
    if slotnum_package:
        slotnum_package = int(slotnum_package)
    else:
        slotnum_package = 0
    _stripe_slotnum_org, _stripe_slotnum_package = get_slots(user)
    if _stripe_slotnum_package is not None:
        MAX = int(_stripe_slotnum_package)
    else:
        MAX = config.USER_SLOTMAX_PACKAGE
    if not slotnum_package < MAX:
        err = 1

#    else:
#        db.incr(config.REDIS_KEY_USER_SLOTNUM_PACKAGE % user)
#    if here is not None and err != 1:
#        packages = get_packages_selected(user)
#        sorted_keys = sorted(
#            [int(i) for i in packages.iterkeys() if i.isdigit()])
#        for key in sorted_keys:
#            if key != int(here):
#                package = packages[str(key)][0]
#                orgset = packages[str(key)][1]
#                get_package_selected(user, package=package,
#                    orgset=orgset, slotset=key)
#            else:
#                get_package_selected(user, remove=True, slotdel=key)
#                package = packages[str(key)][0]
#                orgset = packages[str(key)][1]
#                get_package_selected(user, package=package,
#                    orgset=orgset, slotset=key)
    return err, slotnum_package


# Hosted config files
def buildout():
    """
        Check out repos to file system so we can provide buildout
        configuration files at /buildout/.
    """
    user = config.BUILDOUT_USER
    tempdir = os.path.abspath(tempfile.mkdtemp(prefix='clone-'))
    index = open(os.path.join(tempdir, 'index.html'), 'w')
    index.write(config.BUILDOUT_INDEX)
    index.close()
    if not os.environ.get('SKIP_BUILDOUT'):
        for repo, alias in config.BUILDOUT_REPOS:
            commits = json.loads(
                get_repo_commits(repo, user=user))
            if not 'message' in commits:  # No gh error, ok to proceed
                last_commit = commits[0]['sha']
                tree = json.loads(
                    get_repo_tree(
                        repo,
                        key=last_commit,
                        user=user,
                    )
                )
                write_tree(repo, tree=tree, user=user,
                    alias=alias, tempdir=tempdir)
    return tempdir


def bulk_add(packages, user):
    """
        Support bulk add by processing entries like:

        repo [org]
    """
    added = 0
    i = 0
    packages = packages.split('\n')
    num = len(packages)
    org = None
    results = str()

    db.set(config.REDIS_KEY_USER_SLOTNUM_PACKAGE % user, num)
    results += "Added %s slots.\n" % num

    orgs_selected = db.hgetall(config.REDIS_KEY_USER_ORGS_SELECTED %
        user).items()

    for package in packages:
        try:  # First, try: repo [org]
            package, org = package.split()
            for orgsel in orgs_selected:
                if org == orgsel[1]:
                    get_package_selected(user, package=package,
                        orgset=orgsel[0], slotset=i)
                    results += ("Added %s to slot %s with organization %s.\n" %
                        (package, i + 1, org))
                    added += 1
                    i += 1
        except:  # Next, try: repo
            try:
                package = package.split()
                package = package[0]
                get_package_selected(user, package=package, slotset=i)
                results += "Added %s to slot %s.\n" % (
                    package, i + 1)
                added += 1
                i += 1
            except:  # Give up
                pass

    results += "Added %s packages" % added

    if added == 0:
        results += ", check org slots for matching org?\n"
    else:
        results += ".\n"

    return results


@cache_region('one_day')
def check_docs(package):
    """
        Check for documentation by package name on various sites so
        we can provide links to them from /package/<package> pages.
    """
    results = dict()
    packages = [package, ]  # Check alternate case if it exists
    normalized = get_normalized_package(package)
    if package != normalized:
        packages.append(normalized)
    for source in config.DOCS:
        for package in packages:
            try:  # Be kind when the tubes are down
                url = '%s/%s' % (config.DOCS[source], package)
                response = requests.get(url)
            except:
                return results
            if response.status_code == 200:
                results[source] = ('%s/%s' % (config.DOCS[source],
                    package))
    return results


def check_email(userid):
    """
        Retrieve beta users' email address from database for beta
        validation purposes: only signed up users can
        access beta features.
    """
    whitelist = db.smembers(config.REDIS_KEY_USERS_WHITELIST)
    if not whitelist:  # No whitelist in db
        whitelist = tuple()
    email = db.get('user:%s:email' % userid)
    if email in [db.hget(i, 'email_address')
        for i in db.smembers('beta_users')] or (userid in
            whitelist):
        return True
    else:
        return False


@cache_region('one_day')
def check_exists(package):
    """
        Check to see if a package exists on PyPI.
    """
    try:
        url = '%s/%s' % (config.PYPI_URL, package)
        results = requests.get(url)
    except:
        return False
    if results.status_code == 200:
        return True
    else:
        return False


@cache_region('one_day')
def check_files(package):
    """
        http://crate.io/api/v1/release/Django-1.3.1/?format=json
    """
    results = None
    packages = [package, ]  # Check alternate case if it exists
    normalized = get_normalized_package(package)
    if package != normalized:
        packages.append(normalized)
    version = get_package_version(package)
    for package in packages:
        try:  # Be kind when the tubes are down
            url = config.CRATE_DOWNLOAD_URL % (package, version)
            response = requests.get(url)
        except:
            return results
        if response.status_code == 200:
            try:
                results = json.loads(response.content)['files'][0]['file']
            except:
                results = None
    return results


@cache_region('one_day')
def check_grids(package):
    """
        Return any opencomparise grids that exist for package.
    """
    grids = list()
    package = package.replace('.', '-').lower()  # Normalize for opencomp
    for framework in config.OPENCOMP_FRAMEWORKS:
        try:
            url = config.OPENCOMP_SERVICE_URLS[1] % (framework, package)
            results = requests.get(url)
        except:  # No intertubes
            return grids
        if results.status_code == 200:
            content = json.loads(results.content)
            if 'grids' in content:
                for grid in content['grids']:
                    url = config.OPENCOMP_SERVICE_URLS[0] % framework + grid
                    response = requests.get(url)
                    absolute_url = json.loads(response.content)['absolute_url']
                    grids.append(config.OPENCOMP_SERVICE_URLS[0] %
                        framework + absolute_url)
    return grids


def check_input(package):
    """
        Call regexp on package name.
    """
    if valid_package.match(package) is not None:
        return True
    else:
        return False


def check_metadata(metadata):
    """
        Only return metadata not in ignored list.
    """
    results = dict()
    if metadata is None:
        return results
    for field in metadata:
        if (metadata[field] not in config.METADATA_IGNORE['values'] and
            field not in config.METADATA_IGNORE['fields']):
            results[field] = metadata[field]
    return results


def colanderize(colanderized_items, uncolanderized_items):
    """
        Turn items into something deform can use; allow a colanderized list to
        be passed in and appended to.
    """
    for item in uncolanderized_items:
        colanderized_items.append([item, item])
    return colanderized_items


def config_slots(plan, user):
    """
        Setup initial slot configuration for user.
    """
    org_num = config.PLANS_DATA[plan][2]
    db.set(config.REDIS_KEY_USER_SLOTMAX_ORG % user, org_num)
    package_num = config.PLANS_DATA[plan][3]
    db.set(config.REDIS_KEY_USER_SLOTMAX_PACKAGE % user, package_num)


def create_package(request, slots_org, template, token, userid, org=None):
    """
        Process form input to create new Python package via paster
    """
    error = 0
    name = request.POST['name']
    out = str()
    userid_save = userid  # In case of org
    if check_input(name):
        # Inject orgid as needed
        if org:
            if org in slots_org:
                org = userid = slots_org[org]
        if create_repo(name, org=org, token=token):
            if config.COOKIE_GITHUB in request.session:
                data = request.session[config.COOKIE_GITHUB]
                email = get_email(userid_save)
                fullname = get_name(userid_save)
                if 'username' in data:
                    username = data['username']
                if 'password' in data:
                    password = data['password']
                    password = urllib.quote(password)  # Allow "funny" chars
                tempdir = os.path.abspath(tempfile.mkdtemp(prefix='new-'))
                os.chdir(tempdir)
                url = "https://%s:%s@github.com/%s/%s" % (username,
                    password, userid, name)
                cmd = pbs.Command('/app/vendor/git-1.7.11.1/git')
                cmd('clone', url)
                dist_root, out = paster_create(name, tempdir, userid,
                    template, email, fullname)
                os.chdir(dist_root)
                if os.path.exists('%s.egg-info' % name):
                    shutil.rmtree('%s.egg-info' % name)
                if os.path.exists('setup.cfg'):
                    os.remove('setup.cfg')
                cmd('add', '*')
                cmd('config', 'user.email', "'%s'" % email)
                cmd('config', 'user.name', "'%s'" % fullname)
                try:
                    cmd('commit', '-a', '-m', 'Created by pythonpackages.com')
                except:
                    error = 4  # Repo exists?
                try:
                    cmd('push', 'origin', 'master')
                    #shutil.rmtree(tempdir)
                    get_package_selected(userid, package=name)  # Save
                except:
                    error = 3  # Bad credentials
        else:
            error = 2  # Create repo failed
    else:
        error = 1  # Package name is bad
    if error == 0:
        # Tweet create
        try:
            msg = "%s created by %s %s/%s/%s #python" % (
                name,
                userid_save,
                config.GITHUB_URL,
                userid,
                name,
            )
            if len(msg) <= 140:
                send_tweet(msg)
            else:
                raise Exception
        except:
            # TwitterError
            pass
    return error, out


def create_ref(package, user=None, token=None, sha=None, tag=None):
    """
        POST /repos/:user/:repo/git/refs
    """
    if tag is None and sha is not None:
        tag = sha
    else:
        # XXX tag = random() ?
        pass
    payload = {
        'ref': 'refs/tags/%s' % tag,
        'sha': sha,
    }
    requests.post(config.GITHUB_URL_REPOS_REFS % (user, package, token),
        data=json.dumps(payload))
    return


def create_repo(name, org=None, token=None):
    """
        POST /user/repos
        POST /orgs/:org/repos
    """
    payload = {
        'name': name,
    }
    try:  # XXX Use status code instead of try/except
        if org:
            post = config.GITHUB_URL_ORG_REPOS_NEW % (org, token)
            requests.post(post, data=json.dumps(payload))
        else:
            post = config.GITHUB_URL_REPOS_NEW % token
            requests.post(post, data=json.dumps(payload))
        return True
    except:
        return False


def create_tag(package, user=None, token=None, sha=None, tag=None):
    """
        POST /repos/:user/:repo/git/tags
        Parameters
        tag
            String of the tag
        message
            String of the tag message
        object
            String of the SHA of the git object this is tagging
        type
            String of the type of the object we are tagging.
            Normally this is a commit
            but it can also be a tree or a blob.
        tagger.name
            String of the name of the author of the tag
        tagger.email
            String of the email of the author of the tag
        tagger.date
            Timestamp of when this object was tagged
        """
    if tag is None and sha is not None:
        tag = sha
    else:
        # XXX tag = random() ?
        pass
    message = 'Tag release %s' % tag
    obj = sha
    typ = 'tree'
    name = 'pythonpackages'
    email = 'info@pythonpackages.com'
    date = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    payload = {
        'tag': tag,
        'message': message,
        'object': obj,
        'type': typ,
        'tagger.name': name,
        'tagger.email': email,
        'tagger.date': date,
    }
    requests.post(config.GITHUB_URL_REPOS_TAGS % (user, package, token),
        data=json.dumps(payload))
    create_ref(package, sha=sha, user=user, token=token, tag=tag)
    return


def create_tree(package_dir, package=None, sha=None, token=None, user=None):
    """
        POST /repos/:user/:repo/git/trees

        Parameters

        base_tree
            optional String of the SHA1 of the tree you want to update with new
            data
        tree
            Array of Hash objects (of path, mode, type and sha) specifying a
            tree structure
        tree.path
            String of the file referenced in the tree
        tree.mode
            String of the file mode - one of 100644 for file (blob), 100755 for
            executable (blob), 040000 for subdirectory (tree), 160000 for
            submodule
            (commit) or 120000 for a blob that specifies the path of a symlink
        tree.type
            String of blob, tree, commit
        tree.sha
            String of SHA1 checksum ID of the object in the tree
        tree.content
            String of content you want this file to have - GitHub will write
            this
            blob out and use that SHA for this entry. Use either this or
            tree.sha

        Input

        {
          "tree": [
            {
              "path": "file.rb",
              "mode": "100644",
              "type": "blob",
              "sha": "44b4fc6d56897b048c772eb4087f854f46256132"
            }
          ]
        }
        """
    payload = {
        "tree": [
            {
                "path": "%s" % package_dir,
                "mode": "040000",
                "type": "tree",
                "sha": "%s" % sha,
            }
        ]
    }
    requests.post(config.GITHUB_URL_REPOS_TREE_CREATE % (user, package, token),
        data=json.dumps(payload))


def delete_repo(package, token, user):  # New style, fewer kwargs \o/
    """
        DELETE /repos/:user/:repo
    """
    query = config.GITHUB_URL_REPOS_DELETE % (user, package, token)
    content = requests.delete(query)
    return content


# H/T Richard Jones
def flatten_params(params):
    """
        Convenience method used by rjones' PyPI OAuth1 code
    """
    flattened = []
    for k, v in params.items():
        if isinstance(v, list):
            for v in v:
                if v:
                    flattened.append((k, v))
        elif v:
            flattened.append((k, v))
    return flattened


def get_access_token(code):
    """
        Part of GitHub OAuth dance
    """
    payload = {
        'client_id': config.GITHUB_CLIENT_ID,
        'client_secret': config.GITHUB_CLIENT_SECRET,
        'code': code,
    }
    return requests.post(config.GITHUB_URL_TOKEN, data=payload).content


def get_avatar(user):
    """
        Retrieve gravatar URL from the database.
    """
    return db.get('user:%s:avatar' % user)


def get_beta_count():
    """
        Retrieve number of beta sign ups from the database.
    """
    try:
        num_users = len(db.smembers('beta_users'))
        return locale_format(int(num_users))
    except:
        return 0


def get_blob(package, key=None, token=None, user=None):
    """
        GET /repos/:user/:repo/git/blobs/:sha
    """
    headers = {'Accept': 'application/vnd.github.v3.raw'}
    if token is not None:
        query = config.GITHUB_URL_REPOS_BLOB % (user, package, key, token)
    else:  # No qs bit
        query = config.GITHUB_URL_REPOS_BLOB_ANON % (user, package, key)
    content = requests.get(query, headers=headers).content
    return content


@cache_region('one_hour')
def get_changelog():
    """
        Use yolk API to query package activity on PyPI.
    """
    try:
        # XXX Depends on PyPI
        changelog = yolk.changelog(config.DEFAULT_ACTIVITY_LIMIT)
        changelog.reverse()
        return changelog
    except:
        return list()


def get_email(user):
    """
        Retrieve user's email from the database
    """
    return db.get('user:%s:email' % user)


def get_featured_by(package):
    """
        Retrieve user who last featured package.
    """
    try:
        if db.exists(config.REDIS_KEY_PACKAGE_FEATURED_BY % package):
            return db.lrange(config.REDIS_KEY_PACKAGE_FEATURED_BY % package,
                0, 0)[0]
        else:
            return 'anonymous'
    except:
        # No db
        return 'anonymous'


@cache_region('one_day')
def get_followers():
    """
        Use Twitter API to retrieve number of followers of @pythonpackages.
    """
    try:
        return locale_format(len(twitter.GetFollowers()))
    except:
        # No tubes
        return 0


def get_fortune():
    """
        Get a random fortune off disk. Display in footer.
    """
    return fortune.get_random_fortune(config.FORTUNE_FILE)


def get_logged_in():
    """
        Return a list of users that have signed in.
    """
    try:
        return db.smembers('logged_in')
    except:
        # XXX No db
        return list()


def get_menu(user):
    """
        Return HTML for user menu.
    """
    avatar = get_avatar(user)
    name = get_name(user)
    if avatar is not None:
        avatar = avatar.split('?')[0] + '?s=18'
    return config.MENU % (avatar, name)


def get_name(user):
    """
        Retrieve full name for user from the database.
    """
    try:
        name = db.get('user:%s:name' % user).decode('utf-8')
    except:
        name = db.get('user:%s:name' % user)
    return name


@cache_region('one_day')
def get_normalized_package(package):
    """
        Return normalized package name from PyPI given a package name.
    """
    try:
        # XXX Depends on PyPI
        package = vanity.normalise_project(package)
    except:
        # XXX Package does not exist
        pass
    return package


def get_numbers():
    """
        Convenience function to call other functions to
        return stats from the db.
    """
    return num_downloads(), num_packages(), num_packages_pypi(), \
        num_times_featured()


def get_org_info(org):
    """
        GET /orgs/:org
    """
    query = config.GITHUB_URL_ORG_INFO % org
    response = requests.get(query)
    return response.content


def get_org_repo(org, page, token, search):
    """
        GET /repos/:org/:repo
    """
    # XXX Needs token?
    query = config.GITHUB_URL_ORG_REPO % (org, search)
    response = requests.get(query)
    return response.content


def get_org_repos(org, page, token):
    """
        GET /orgs/:org/repos
    """
    # XXX Needs token?
    query = config.GITHUB_URL_ORG_REPOS % (org, page)
    response = requests.get(query)
    return response.content


def get_org_selected(user, org=None, remove=False, slotset=None,
    slotget=None, slotdel=None):
    """
        Retrieve org selected by user from the database.
    """
    if remove:
        db.hdel(config.REDIS_KEY_USER_ORGS_SELECTED % user, slotdel)
    if org is None:
        org = db.hget(config.REDIS_KEY_USER_ORGS_SELECTED % user, slotget)
    else:
        db.hset(config.REDIS_KEY_USER_ORGS_SELECTED % user, slotset, org)
    return org


def get_orgs_selected(user):
    return db.hgetall(config.REDIS_KEY_USER_ORGS_SELECTED % user)


# Vain-cheese-a-like
@cache_region('one_day')
def get_package_downloads(package):
    """
        Use PyPI API to retrieve package download count (if package is
        hosted on PyPI).
    """
    try:
        db.ping()
    except:
        return 0
    if db.exists(config.REDIS_KEY_PACKAGE_DOWNLOADS % package):
        downloads = db.get(config.REDIS_KEY_PACKAGE_DOWNLOADS % package)
        if downloads:
            downloads = int(downloads)
        else:
            downloads = 0
        return downloads
    else:
        try:
            # XXX Depends on PyPI
            downloads = vanity.downloads_total(package)
            db.set(config.REDIS_KEY_PACKAGE_DOWNLOADS % package, downloads)
            db.expire(config.REDIS_KEY_PACKAGE_DOWNLOADS % package,
                config.REDIS_EXPIRE_ONE_DAY)
            return int(downloads)
        except:
            return 0


@cache_region('one_hour')
def get_package_metadata(package, version):
    """
        Retrieve package metadata from PyPI via yolk, save to database.
    """
    # XXX Depends on PyPI and db
    metadata = list()
    try:
        if db.exists(config.REDIS_KEY_PACKAGE_METADATA % package):
            return json.loads(db.get(
                config.REDIS_KEY_PACKAGE_METADATA % package))
        else:
            metadata = yolk.release_data(package, version)
            db.set(config.REDIS_KEY_PACKAGE_METADATA % package,
                json.dumps(metadata))
            db.expire(config.REDIS_KEY_PACKAGE_METADATA % package,
                config.REDIS_EXPIRE_ONE_DAY)
        return metadata
    except:
        return metadata


def get_package_score(sorted_set, package):
    """
        Retrieve number of times a package has been featured from the database.
    """
    try:
        db.ping()
    except:
        return 0
    score = db.zscore(sorted_set, package)
    if score is not None:
        score = int(score)
    else:
        score = 0
    return locale_format(score)


def get_package_selected(user, orgset=None, package=None, remove=False,
    slotset=None, slotget=None, slotdel=None):
    """
        Get/set package selected by user from the database.
    """
    if remove:
        db.hdel(config.REDIS_KEY_USER_PACKAGES_SELECTED % user, slotdel)
        return
    if package is None:
        package = db.hget(config.REDIS_KEY_USER_PACKAGES_SELECTED % user,
            slotget)
    else:
        payload = (package, orgset)
        payload = json.dumps(payload)
        db.hset(config.REDIS_KEY_USER_PACKAGES_SELECTED % user, slotset,
            payload)
    return package


@cache_region('one_hour')
def get_package_version(package):
    """
        Use PyPI API (via yolk) to get the latest version of a package.
    """
    # XXX Depends on PyPI and db
    version = '0.0.0'
    try:
        if db.exists(config.REDIS_KEY_PACKAGE_VERSION % package):
            return db.get(config.REDIS_KEY_PACKAGE_VERSION % package)
        else:
            version = yolk.query_versions_pypi(package)
            try:
                version = version[1][0]  # annoying
            except:
                version = '0.0.0'
            db.set(config.REDIS_KEY_PACKAGE_VERSION % package, version)
            db.expire(config.REDIS_KEY_PACKAGE_VERSION % package,
                config.REDIS_EXPIRE_ONE_HOUR)
            return version
    except:
        return version


def get_packages_selected(user):
    """
        Get list of packages selected for user from the database.
    """
    results = db.hgetall(config.REDIS_KEY_USER_PACKAGES_SELECTED % user)
    for result in results:
        results[result] = json.loads(results[result])
    return results


def get_permission_map(request=None):
    """
        Return list of permissions for user for use in templates.
    """
    permissions = {}
    if request is None:  # No perm
        for perm in config.PERMS:
            permissions[perm] = None
        return permissions
    for perm in config.PERMS:
        permissions[perm] = has_permission(perm, request.root, request)
    return permissions


def get_plan(user):
    """
        Retrieve the plan selected by user from the database.
    """
    plan = db.get(config.REDIS_KEY_USER_PLAN % user)
    if plan is None:
        plan = 'free'
    return plan


def get_python3_status(classifiers):
    """
        Search through list of classifiers for a Python 3 classifier.
    """
    status = False
    for classifier in classifiers:
        if classifier.find('Programming Language :: Python :: 3') == 0:
            status = True
    return status


def get_query_string(request):
    """
        Return the query string if it exists in the request.
    """
    query_string = ''
    if 'QUERY_STRING' in request:
        query_string = request['QUERY_STRING']
    return query_string


@cache_region('one_hour')
def get_releases():
    """
        Use PyPI API (via yolk) to retrieve a list of recently released
        packages.
    """
    try:
        # XXX Depends on PyPI
        return yolk.updated_releases(config.DEFAULT_ACTIVITY_LIMIT)
    except:
        return list()


def get_repo_commits(package, user=None, token=None):
    """
        GET /repos/:user/:repo/commits
    """
    query = config.GITHUB_URL_REPOS_COMMITS % (user, package, token)
    content = requests.get(query).content
    return content


def get_repo_tree(package, key=None, token=None, user=None):
    """
        GET /repos/:user/:repo/git/trees/:sha?recursive=1
    """
    query = config.GITHUB_URL_REPOS_TREE % (user, package, key, token)
    content = requests.get(query).content
    return content


def get_response():
    """
        Configure default response for use in templates.
    """
    return {
        'betacount': 0,
        'count': 0,
        'colors': list(),
        'discuss': False,
        'error': False,
        'entries': list(),
        'flash': str(),
        'followers': 0,
        'fortune': None,
        'form': None,
        'freeslot_org': None,
        'freeslot_package': None,
        'menu': str(),
        'most_downloads': list(),
        'most_vain': list(),
        'num_downloads': 0,
        'num_times_featured': 0,
        'num_packages': 0,
        'num_packages_pypi': 0,
        'num_repos': 0,
        'orgs_selected': list(),
        'package': str(),
        'package_selected': False,
        'password': str(),
        'permissions': get_permission_map(),
        'recent_entries': list(),
        'recent_troves': list(),
        'recent_users': list(),
        'releases': list(),
        'slot': 0,
        'slotnum_org': int(),
        'slotnum_package': int(),
        'slots_org': dict(),
        'slots_package': dict(),
        'submitted': False,
        'timestamp': str(),
        'timestamp_msg': str(),
        'tree': None,
        'url': str(),
        'userid': str(),
        'userlink': str(),
        'username': str(),
        'user_list': list(),
    }


def get_slot_info(user):
    """
        Retrieve slot info for user from the database.
    """
    # XXX freeslot is deprecated.
    freeslot_org = get_org_selected(user)
    freeslot_package = get_package_selected(user)
    slotnum_org = db.get(
        config.REDIS_KEY_USER_SLOTNUM_ORG % user)
    slotnum_org_stripe = db.get(
        config.REDIS_KEY_USER_SLOTMAX_ORG % user)
    if slotnum_org:
        slotnum_org = int(slotnum_org)
    if slotnum_org_stripe:
        slotnum_org_stripe = int(slotnum_org_stripe)
    slots_org = get_orgs_selected(user)
    slots_package = get_packages_selected(user)
    slotnum_package = db.get(
        config.REDIS_KEY_USER_SLOTNUM_PACKAGE % user)
    slotnum_package_stripe = db.get(
        config.REDIS_KEY_USER_SLOTMAX_PACKAGE % user)
    if slotnum_package:
        slotnum_package = int(slotnum_package)
    if slotnum_package_stripe:
        slotnum_package_stripe = int(slotnum_package_stripe)
    return freeslot_org, freeslot_package, slotnum_org, slotnum_org_stripe, \
        slots_org, slots_package, slotnum_package, slotnum_package_stripe


def get_slots(user):
    """
        Return the number of org and package slots for the user from the
        database.
    """
    org = None
    package = None
    if db.exists(config.REDIS_KEY_USER_SLOTMAX_ORG % user):
        org = db.get(config.REDIS_KEY_USER_SLOTMAX_ORG % user)
    if db.exists(config.REDIS_KEY_USER_SLOTMAX_PACKAGE % user):
        package = db.get(config.REDIS_KEY_USER_SLOTMAX_PACKAGE % user)
    return org, package


def get_stats(criteria=None, limit=None, user=None):
    """
        Workhorse function to pull various statistics out of redis e.g.
        list of packages featured by user.
    """
    if limit is None:
        limit = config.DEFAULT_LIMIT
    results = OrderedDict()
    # Based on http://tools.assembla.com/yolk/browser/trunk/yolk/cli.py#L446
    if criteria == 'changelog':
        changelog = get_changelog()
        last_pkg = str()
        for pkg, ver, num, msg in changelog:
            downloads = get_package_downloads(pkg)
            if ver is None:
                ver = get_package_version(pkg)  # Requires PyPI
            metadata = get_package_metadata(pkg, ver)  # Requires PyPI
            if 'classifiers' in metadata:
                classifiers = metadata['classifiers']
            else:
                classifiers = list()
            if 'summary' in metadata:
                summary = metadata['summary']
            else:
                summary = str()
            python3_status = get_python3_status(classifiers)
            score = get_package_score(config.REDIS_KEY_PACKAGES_FEATURED, pkg)
            if pkg != last_pkg:
                results[pkg] = {
                    'featured_count': locale_format(score),
                    'package_downloads': locale_format(downloads),
                    'package_classifiers': classifiers,
                    'python3_status': python3_status,
                    'messages': [msg, ],
                    'name': pkg,
                    'num': num,
                    'package_summary': summary,
                    'version': ver,
                }
                last_pkg = pkg
            else:
                results[pkg]['messages'].append(msg)
    elif criteria == 'dashboard':
        for item in db.lrange(config.REDIS_KEY_RELEASES_ENTERED_USER % user, 0,
            limit):
            downloads = get_package_downloads(item)
            featured_by = get_featured_by(item)
            score = get_package_score(config.REDIS_KEY_PACKAGES_FEATURED, item)
            version = get_package_version(item)  # Requires PyPI
            metadata = get_package_metadata(item, version)  # Requires PyPI
            if 'classifiers' in metadata:
                classifiers = metadata['classifiers']
            else:
                classifiers = list()
            if 'summary' in metadata:
                summary = metadata['summary']
            else:
                summary = str()
            package_quality, trash_report = get_trash_report(item)
            python3_status = get_python3_status(classifiers)
            timestamp = get_timestamp(item, release=True)
            results[item] = {
                'featured_by': featured_by,
                'featured_count': locale_format(score),
                'package_classifiers': classifiers,
                'package_classifiers_num': len(classifiers),
                'package_summary': summary,
                'package_downloads': locale_format(downloads),
                'package_quality': package_quality,
                'package_version': version,
                'python3_status': python3_status,
                'timestamp': timestamp,
                'trash_report': trash_report,
            }
    elif criteria == 'downloaded':
        for item, downloads in db.zrevrange(
            config.REDIS_KEY_PACKAGES_DOWNLOADED, 0, limit, 'WITHSCORES'):
            featured_by = get_featured_by(item)
            version = get_package_version(item)  # Requires PyPI
            metadata = get_package_metadata(item, version)  # Requires PyPI
            if 'classifiers' in metadata:
                classifiers = metadata['classifiers']
            else:
                classifiers = list()
            if 'summary' in metadata:
                summary = metadata['summary']
            else:
                summary = str()
            package_quality, trash_report = get_trash_report(item)
            python3_status = get_python3_status(classifiers)
            score = get_package_score(config.REDIS_KEY_PACKAGES_FEATURED, item)
            results[item] = {
                'featured_by': featured_by,
                'featured_count': locale_format(score),
                'package_classifiers': classifiers,
                'package_classifiers_num': len(classifiers),
                'package_summary': summary,
                'package_downloads': locale_format(downloads),
                'package_quality': package_quality,
                'package_version': version,
                'python3_status': python3_status,
                'trash_report': trash_report,
            }
    elif criteria == 'entries':
        for item in db.lrange(config.REDIS_KEY_PACKAGES_ENTERED, 0, limit):
            downloads = get_package_downloads(item)
            featured_by = get_featured_by(item)
            version = get_package_version(item)  # Requires PyPI
            metadata = get_package_metadata(item, version)  # Requires PyPI
            if 'classifiers' in metadata:
                classifiers = metadata['classifiers']
            else:
                classifiers = list()
            if 'summary' in metadata:
                summary = metadata['summary']
            else:
                summary = str()
            package_quality, trash_report = get_trash_report(item)
            python3_status = get_python3_status(classifiers)
            score = get_package_score(config.REDIS_KEY_PACKAGES_FEATURED, item)
            timestamp = get_timestamp(item)
            results[item] = {
                'featured_by': featured_by,
                'featured_count': locale_format(score),
                'package_classifiers': classifiers,
                'package_classifiers_num': len(classifiers),
                'package_summary': summary,
                'package_downloads': locale_format(downloads),
                'package_quality': package_quality,
                'package_version': version,
                'python3_status': python3_status,
                'timestamp': timestamp,
            }
    elif criteria == 'featured':
        for item, score in db.zrevrange(config.REDIS_KEY_PACKAGES_FEATURED,
            0, limit, 'WITHSCORES'):
            downloads = get_package_downloads(item)
            featured_by = get_featured_by(item)
            version = get_package_version(item)  # Requires PyPI
            metadata = get_package_metadata(item, version)  # Requires PyPI
            if 'classifiers' in metadata:
                classifiers = metadata['classifiers']
            else:
                classifiers = list()
            if 'summary' in metadata:
                summary = metadata['summary']
            else:
                summary = str()
            package_quality, trash_report = get_trash_report(item)
            python3_status = get_python3_status(classifiers)
            timestamp = get_timestamp(item)
            results[item] = {
                'featured_by': featured_by,
                'featured_count': locale_format(score),
                'package_classifiers': classifiers,
                'package_classifiers_num': len(classifiers),
                'package_summary': summary,
                'package_downloads': locale_format(downloads),
                'package_quality': package_quality,
                'package_version': version,
                'python3_status': python3_status,
                'timestamp': timestamp,
                'trash_report': trash_report,
            }
    elif criteria == 'featured_user':
        for item in db.lrange(
            config.REDIS_KEY_PACKAGES_ENTERED_USER % user,
                0, limit):
            downloads = get_package_downloads(item)
            featured_by = get_featured_by(item)
            version = get_package_version(item)  # Requires PyPI
            metadata = get_package_metadata(item, version)  # Requires PyPI
            if 'classifiers' in metadata:
                classifiers = metadata['classifiers']
            else:
                classifiers = list()
            if 'summary' in metadata:
                summary = metadata['summary']
            else:
                summary = str()
            package_quality, trash_report = get_trash_report(item)
            python3_status = get_python3_status(classifiers)
            score = get_package_score(config.REDIS_KEY_PACKAGES_FEATURED_USER %
                user, item)
            results[item] = {
                'featured_by': featured_by,
                'featured_count': locale_format(score),
                'package_classifiers': classifiers,
                'package_classifiers_num': len(classifiers),
                'package_summary': summary,
                'package_downloads': locale_format(downloads),
                'package_quality': package_quality,
                'package_version': version,
                'python3_status': python3_status,
                'trash_report': trash_report,
            }
    elif criteria == 'releases':
        releases = get_releases()
        for package, version in releases:
            downloads = get_package_downloads(package)
            metadata = get_package_metadata(package, version)  # Requires PyPI
            if 'summary' in metadata:
                summary = metadata['summary']
            else:
                summary = str()
            score = get_package_score(config.REDIS_KEY_PACKAGES_FEATURED,
                package)
            results[package] = {
                'featured_count': locale_format(score),
                'package_downloads': locale_format(downloads),
                'package_summary': summary,
                'version': version,
            }
    elif criteria == 'trove':
        for item, score in db.zrevrange(
            config.REDIS_KEY_TROVE_CLASSIFIERS_FEATURED, 0, limit,
            'WITHSCORES'):
            results[item] = locale_format(score)
    elif criteria == 'user':
        for item in db.lrange(config.REDIS_KEY_PACKAGES_ENTERED_USER % user, 0,
            limit):
            downloads = get_package_downloads(item)
            featured_by = get_featured_by(item)
            version = get_package_version(item)  # Requires PyPI
            metadata = get_package_metadata(item, version)  # Requires PyPI
            if 'classifiers' in metadata:
                classifiers = metadata['classifiers']
            else:
                classifiers = list()
            if 'summary' in metadata:
                summary = metadata['summary']
            else:
                summary = str()
            package_quality, trash_report = get_trash_report(item)
            python3_status = get_python3_status(classifiers)
            score = get_package_score(config.REDIS_KEY_PACKAGES_FEATURED_USER %
                user, item)
            timestamp = get_timestamp(item)
            results[item] = {
                'featured_by': featured_by,
                'featured_count': locale_format(score),
                'package_classifiers': classifiers,
                'package_classifiers_num': len(classifiers),
                'package_summary': summary,
                'package_downloads': locale_format(downloads),
                'package_quality': package_quality,
                'package_version': version,
                'python3_status': python3_status,
                'timestamp': timestamp,
                'trash_report': trash_report,
            }
    elif criteria == 'users':
        for user in db.lrange(config.REDIS_KEY_USERS_ENTERED, 0, limit):
            score = get_package_score(config.REDIS_KEY_USERS_FEATURED, user)
            # Recursion FTW \o/
            package_list = get_stats(criteria='featured_user', limit=5,
                user=user)
            results[user] = {
                'package_count': locale_format(score),
                'package_list': package_list,
            }
    elif criteria == 'user_list':
        for user, score in db.zrevrange(config.REDIS_KEY_USERS_FEATURED, 0,
            limit, 'WITHSCORES'):
            results[user] = locale_format(score)
    return results


def get_timestamp(package, release=False):
    """
        Return timestamp for package featuring or release
        from the database.
    """
    if release:
        key = config.REDIS_KEY_PACKAGE_RELEASED_TIME
    else:
        key = config.REDIS_KEY_PACKAGE_FEATURED_TIME
    try:
        if db.exists(key % package):
            return db.lrange(key % package, 0, 0)[0]
        else:
            return 'unknown time'
    except:
        # No db
        return 'unknown time'


@cache_region('one_day')
def get_trash_report(package):
    """
        Use PyPI API (via trashfinder) to check package sanity.
    """
    package_quality, trash_report = True, list()
    try:
        if db.exists(config.REDIS_KEY_PACKAGE_TRASH % package):
            trash_report = json.loads(db.get(config.REDIS_KEY_PACKAGE_TRASH
                % package))
        else:
            # XXX Depends on PyPI
            trash_report = process_package(package)
            db.set(config.REDIS_KEY_PACKAGE_TRASH % package,
                json.dumps(trash_report))
            db.expire(config.REDIS_KEY_PACKAGE_TRASH % package,
                config.REDIS_EXPIRE_ONE_HOUR)
    except:
        # XXX PyPI or db down
        pass
    if len(trash_report) > 0:
        package_quality = False
    return package_quality, trash_report


def get_user_id(userinfo):
    """
        Retrieve user id from GitHub APIv3 call results.
    """
    avatar = email = name = userid = None
    if 'avatar_url' in userinfo:
        avatar = userinfo['avatar_url']
    if 'email' in userinfo:
        email = userinfo['email']
    if 'login' in userinfo:
        userid = userinfo['login']
    if 'name' in userinfo:
        name = userinfo['name']
    return avatar, email, name, userid


def get_user_info(token):
    """
        Send request to GitHub APIv3 to get user info and return
        results.
    """
    return requests.get(config.GITHUB_URL_USER % token).content


def get_user_orgs(token):
    """
        Send request to GitHub APIv3 to get user orgs and return
        results.
    """
    return requests.get(config.GITHUB_URL_USER_ORGS % token).content


def get_user_repo(token, search, user):
    """
        Send request to GitHub APIv3 to get one user repo and return
        results.
    """
    query = config.GITHUB_URL_USER_REPO % (user, search, token)
    content = requests.get(query).content
    return content


def get_user_repos(token):
    """
        Send request to GitHub APIv3 to get user repos and return
        results.
    """
    query = config.GITHUB_URL_USER_REPOS % token
    content = requests.get(query).content
    return content


def get_user_token(userid):
    """
        Retrieve user token from database.
    """
    return db.get('user:%s:token' % userid)


def get_version(package_dir):
    """
        Use distutils2 to retrieve package version.
    """
    mkcfg(package_dir)
    # Open setup.cfg
    filename = '/'.join([package_dir, 'setup.cfg'])
    infile = open(filename)
    cp = ConfigParser.SafeConfigParser()
    cp.readfp(infile)
    infile.close()
    version = cp.get('metadata', 'version')
    # Clean up
    os.remove(filename)
    return version


def get_whitelisted_users():
    """
        Retrieve white listed beta users from the database i.e.
        users allowed to access beta features without signing
        up.
    """
    return db.get(config.REDIS_KEY_WHITELISTED_USERS)


def is_site_user(user):
    """
        Check to see if user has ever logged in and return
        boolean result.
    """
    return db.sismember('site_users', user)


@cache_region('one_day')
def list_packages():
    """
        Use PyPI API to list all the packages.
    """
    try:
        return pypi.list_packages()
    except:
        return


def locale_format(num):
    """
        Given a number e.g. 3000 return formatted number e.g. 3,000.
    """
    try:
        return locale.format("%d", num, grouping=True)
    except:  # XXX Format failed
        return num


def logged_out(user=None):
    """
        If user is None remove user from list of logged in users.
    """
    if user is not None:
        db.srem('logged_in', user)
        return


def mkcfg(package_dir):
    """
        Distutils2 code to convert setup.py to setup.cfg.
    """
    mkcfg = d2.MainProgram()
    mkcfg.load_existing_setup_script(parent_dir=package_dir)
    mkcfg.write_setup_script(parent_dir=package_dir)


def no_sign_in():
    """
        Return sign in HTML for anonymous users.
    """
    return config.MENU_SIGNIN % config.GITHUB_URL_AUTH


@cache_region('one_day')
def num_downloads():
    """
        Calculate and return the total number of downloads from packages
        stored in the database.
    """
    num = 0
    try:
        for package in db.zrange(config.REDIS_KEY_PACKAGES_DOWNLOADED, 0, -1):
            num += int(db.zscore(config.REDIS_KEY_PACKAGES_DOWNLOADED,
            package))
    except:
        # XXX No db
        pass
    return locale_format(num)


def num_packages(formatted=True):
    """
        Calculate and return the number of packages saved in the database i.e.
        number of packages featured.
    """
    try:
        num = len(db.zrange(config.REDIS_KEY_PACKAGES_DOWNLOADED, 0, -1))
        if formatted:
            return locale_format(int(num))
        else:
            return int(num)
    except:
        # XXX No db
        return 0


def num_packages_pypi(formatted=True):
    """
        Calculate and return the number of packages currently hosted on PyPI.
        If we do not have stored in the database, retrieve it from PyPI.
    """
    try:
        if not db.exists(config.REDIS_KEY_NUM_PACKAGES_PYPI):
            packages = list_packages()
            num = len(packages)
            db.set(config.REDIS_KEY_NUM_PACKAGES_PYPI, num)
            db.expire(config.REDIS_KEY_NUM_PACKAGES_PYPI,
                config.REDIS_EXPIRE_ONE_DAY)
        else:
            num = db.get('num_packages_pypi')

        if formatted:
            return locale_format(int(num))
        else:
            return int(num)
    except:
        # XXX No db
        return 0


def num_times_featured(formatted=True):
    """
        Return the number of times a package has been featured from the
        database.
    """
    try:
        db.ping()
    except:
        return 0
    num = db.get(config.REDIS_KEY_PACKAGES_FEATURED_COUNT)
    if num is not None:
        num = int(num)
    else:
        num = 0
    if formatted:
        return locale_format(num)
    else:
        return num


def paster_create(package, tempdir, user, template, email, fullname):
    """
        Run paster to create a new package given a template and user info.
    """
    dist_root = os.path.join(tempdir, package)
    name = get_name(user)
    email = get_email(user)
    url = '%s/%s/%s' % (config.GITHUB_URL, user, package)
    conffile = os.path.join(tempdir, 'pastescript.ini')
    paster_config = config.PASTER_CONFIG % (name, email, url)
    conf = open(conffile, 'w')
    # XXX Kill me
    try:
        conf.write(paster_config.encode('utf-8'))
    except:
        paster_config = config.PASTER_CONFIG % ('', email, url)
        conf.write(paster_config)
    conf.close()
    os.chdir(tempdir)
    # Support pyramid's pcreate
    if template in ('alchemy', 'starter', 'zodb'):
        out = pbs.pcreate('-t', template, package)
    else:
        out = pbs.paster('create', '-t', template, '--config=%s' %
            conffile, '--no-interactive', package)
    manifest = open(os.path.join(dist_root, 'MANIFEST.in'), 'w')
    try:  # Handle namespace packages
        parts = package.split('.')
        parent_dir = parts[0]
    except:
        parent_dir = package
    manifest.write(config.MANIFEST_IN % parent_dir)
    manifest.close()
    return dist_root, out._stdout


def put_repos_in_form(page, token, org, permissions, slots_org, slot,
    search=None, user=None):
    """
        Convenience method to load deform form with choices, based on results
        from GitHub APIv3.
    """
    choices = list()
    num_repos = 0
    schema = None
    if org is None:
        # XXX No page support here yet
        if search:
            if user:
                user_repos = json.loads(get_user_repo(token, search, user))
        else:
            user_repos = json.loads(get_user_repos(token))
        if not 'message' in user_repos:  # No gh error, ok to proceed
            num_repos = len(user_repos)
            if search:
                choices = colanderize(list(), [user_repos['name'], ])
            else:
                choices = colanderize(list(), [repo['name'] for repo in
                    user_repos])
            choices.sort()
            repository = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.RadioChoiceWidget(values=choices),
                name='repository',
                )
            schema = colander.SchemaNode(colander.Mapping())
            schema.add(repository)
    else:
        if str(org) in slots_org:
            if search:
                org_repos = json.loads(get_org_repo(slots_org[str(org)],
                    page, token, search))
            else:
                org_repos = json.loads(get_org_repos(slots_org[str(org)],
                    page, token))
            if not 'message' in org_repos:  # No gh error, ok to proceed
                num_repos = len(org_repos)
                org_info = get_org_info(slots_org[str(org)])
                org_info = json.loads(org_info)
                if not 'message' in org_info:  # No gh error, ok to proceed
                    if 'public_repos' in org_info:
                        num_repos = org_info['public_repos']
                if search:
                    choices = colanderize(list(), [org_repos['name'], ])
                else:
                    choices = colanderize(list(), [repo['name'] for repo in
                        org_repos])
                choices.sort()
            repository = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.RadioChoiceWidget(values=choices),
                name='repository',
                )
            schema = colander.SchemaNode(colander.Mapping())
            schema.add(repository)
    action = str()
    if org >= 0:
        action = "/manage/package?slot=%s&org=%s" % (slot, org)
    if permissions['manage_site']:  # Site managers can remove repo
#        buttons = ('select', 'remove repository', 'remove slot')
        buttons = ('select', 'remove slot')
    else:
        buttons = ('select', 'remove slot')
    if schema is None:  # Return empty form
        schema = colander.SchemaNode(colander.Mapping())
        num_repos = 0
    myform = deform.Form(schema, action=action, buttons=buttons)
    return myform, num_repos


# H/T Richard Jones
def pypi_oauth_register(userid, name, version, summary, **optional):
    '''Register a new package, or release of an existing package.

The "optional" parameters match fields in PEP 345.

The complete list of parameters are:

Single value: description, keywords, home_page, author, author_email,
maintainer, maintainer_email, license, requires_python

Multiple values: requires, provides, obsoletes, requires_dist,
provides_dist, obsoletes_dist, requires_external, project_url,
classifiers.

For parameters with multiple values, pass them as lists of strings.

The API will default metadata_version to '1.2' for you. The other valid
value is '1.0'.

Two additional metadata fields are available specific to PyPI:

1. _pypi_hidden: If set to '1' the relase will be hidden from listings and
searches.
2. bugtrack_url: This will be displayed on package pages.
'''
    auth = requests.auth.OAuth1(config.PYPI_OAUTH_CONSUMER_KEY,
        config.PYPI_OAUTH_CONSUMER_SECRET,
        unicode(db.get(config.REDIS_KEY_USER_PYPI_OAUTH_TOKEN % userid)),
        unicode(db.get(config.REDIS_KEY_USER_PYPI_OAUTH_SECRET % userid)),
        signature_type='auth_header')
    params = {u'name': name, u'version': version, u'summary': summary}
    params.update(optional)
    data = flatten_params(params)
    response = requests.post(config.PYPI_URL_OAUTH_ADD_RELEASE, data=data,
        auth=auth, verify=False)
    return response.content


# H/T Richard Jones
def pypi_oauth_test(userid):
    '''Access the test resource passing optional parameters.

The test resource will echo back the authenticated user and any parameters
we pass.
'''
    auth = requests.auth.OAuth1(config.PYPI_OAUTH_CONSUMER_KEY,
        config.PYPI_OAUTH_CONSUMER_SECRET,
        unicode(db.get(config.REDIS_KEY_USER_PYPI_OAUTH_TOKEN % userid)),
        unicode(db.get(config.REDIS_KEY_USER_PYPI_OAUTH_SECRET % userid)),
        signature_type='auth_header')
    response = requests.get(config.PYPI_URL_OAUTH_TEST, auth=auth,
        verify=False)
    if response.status_code == 200:
        return True
    else:
        return False


# H/T Richard Jones
def pypi_oauth_upload(userid, name, version, content, filename, filetype,
    **optional):
    '''Upload a file for a package release. If the release does not exist then
it will be registered automatically.

The name and version identify the package release to upload the file
against. The content and filetype are specific to the file being uploaded.

content - an readable file object
filetype - one of the standard distutils file types ("sdist", "bdist_win",
etc.)

There are several optional parameters:

pyversion - specify the 'N.N' Python version the distribution works with.
This is not needed for source distributions but required otherwise.
comment - use if there's multiple files for one distribution type.
md5_digest - supply the MD5 digest of the file content to verify
transmission
gpg_signature - ASCII armored GPG signature for the file content
protocol_version - defaults to "1" (currently the only valid value)

Additionally the release parameters are as specified for release() above.
'''
    auth = requests.auth.OAuth1(config.PYPI_OAUTH_CONSUMER_KEY,
        config.PYPI_OAUTH_CONSUMER_SECRET,
        unicode(db.get(config.REDIS_KEY_USER_PYPI_OAUTH_TOKEN % userid)),
        unicode(db.get(config.REDIS_KEY_USER_PYPI_OAUTH_SECRET % userid)),
        signature_type='auth_header')
    params = dict(name=name, version=version, filename=filename,
        filetype=filetype, protocol_version='1', comment='', md5_digest='',
        gpg_signature='')
    params.update(optional)
    for k in list(params):
        if not params[k]:
            del params[k]
    files = dict(content=(filename, content))
    response = requests.post(config.PYPI_URL_OAUTH_UPLOAD, params=params,
        files=files, auth=auth, verify=False)
    return response.content


def release_package(orgset, package, action, slots_org, token,
    userid, ttw=False, slot=None):
    """
        The main attraction to pythonpackages.com: "clone" repo from
        github and then do one of the following:
        - Run Test Suite
        - Tag and Release
        - Test Installation
        - Upload to Test Index
    """
    err = str()
    username = password = None
    # Inject orgid as needed
    userid_save = userid  # In case of org
    if orgset is not None:
        if str(orgset) in slots_org:
            userid = slots_org[str(orgset)]
    commits = json.loads(get_repo_commits(package, user=userid,
        token=token))
    last_commit = None
    if not 'message' in commits:  # No gh error, ok to proceed
        last_commit = commits[0]['sha']
    tree = json.loads(get_repo_tree(package, key=last_commit,
        token=token, user=userid))
    if 'sha' in tree:
        sha = tree['sha']
    else:  # XXX Is this the right thing to do here?
        sha = last_commit
    tempdir = write_tree(package, tree=tree, user=userid,
        token=token)
    package_dir = os.path.join(tempdir, package)
    os.chdir(package_dir)
    os.environ['HOME'] = package_dir  # Configure auth
    filename = os.path.join(package_dir, '.pypirc')
    pypirc = open(filename, 'w')
    tweet = False
    if action == 'upload-to-test-index':
        pypirc.write(config.PYPIRC_TEST % (username, password,
            username, password))
    else:
        pypirc.write(config.PYPIRC % (username, password))
    pypirc.close()
    env = None
    if 'PYTHONHOME' in os.environ:
        env = os.environ['PYTHONHOME']  # Save env
        del(os.environ['PYTHONHOME'])  # Remove env for virtualenv
    pbs.python('/app/virtualenv.py', '--distribute', '.')
    cmd = pbs.Command('bin/python')
    # Make release
    if action == 'test-installation':
        try:
            out = cmd('setup.py', 'install', _err_to_out=True)
            err += out._stdout
        except:
            typ, out, tb = sys.exc_info()
            err += out.message
    if action == 'upload-to-test-index':
        try:
            out = cmd('setup.py', 'register', 'sdist',
                '--formats=zip', 'upload', '-r', 'other', _err_to_out=True)
            err += out._stdout
        except:
            typ, out, tb = sys.exc_info()
            err += out.message
    if action == 'run-test-suite':
        try:
            out = cmd('setup.py', 'test', _err_to_out=True)
            err += out._stdout
        except:
            typ, out, tb = sys.exc_info()
            err += out.message
    if action == 'tag-and-release':
        version = get_version(package_dir)  # distutils2 pysetup
        if ttw:
            # Check credentials
            if not pypi_oauth_test(userid_save):
                return err
        # Tag release
        try:
            create_tag(package, sha=sha, user=userid, token=token,
                tag=version)
        except:
            typ, out, tb = sys.exc_info()
            err += out.message
        # Upload release
        try:
            out = cmd('setup.py', 'sdist', '--formats=zip', _err_to_out=True)
            err = out._stdout
            filename = '%s-%s.zip' % (package, version)
            fqpath = os.path.join(package_dir, 'dist', filename)
            content = open(fqpath)
            err += pypi_oauth_register(userid_save, package, version, package)
            err += pypi_oauth_upload(userid_save, package, version, content,
                filename, 'sdist')
            tweet = True
        except:
            typ, out, tb = sys.exc_info()
            err += out.message
        if tweet:
            # Tweet and score release
            score_release(package, userid)
            try:
                msg = "%s %s released by %s %s/%s/%s #python" % (
                    package,
                    version,
                    userid,
                    config.PYPI_URL,
                    package,
                    version,
                )
                if len(msg) <= 140:
                    send_tweet(msg)
                else:
                    raise Exception
            except:
                # TwitterError
                pass
    if action == 'add-slot-here':
        add_package_slot(userid_save, here=slot)
        err += "Added slot %s below slot %s" % (str(slot + 2), str(slot + 1))

    # Clean up
    if 'PYTHONHOME' in os.environ:
        os.environ['PYTHONHOME'] = env  # Restore env
    return err


def remove_slot(slot, slots, user, org=False):
    """
        Remove a slot
    """
    if org:
        SLOTNUM = config.REDIS_KEY_USER_SLOTNUM_ORG
        SELECTED = config.REDIS_KEY_USER_ORGS_SELECTED
    else:
        SLOTNUM = config.REDIS_KEY_USER_SLOTNUM_PACKAGE
        SELECTED = config.REDIS_KEY_USER_PACKAGES_SELECTED
    db.decr(SLOTNUM % user)
    slotnum = db.get(SLOTNUM % user)
    slotnum = int(slotnum)
    slotmap = {}
    for s in slots.keys():
        if s != 'None':  # Should be None?
            s = int(s)  # Make sure int
            slot = int(slot)  # Make sure int
            if s > slot:
                slotmap[s] = db.hget(SELECTED % user, s)
    for s in slotmap.keys():
        db.hset(SELECTED % user, s - 1, slotmap[s])
    for s in slotmap.keys():
        db.hdel(SELECTED % user, s)


def save_customer(customer, user):
    """
        Called during Stripe processing to save customer in database.
    """
    db.set(config.REDIS_KEY_USER_CUSTOMER % user, customer)


def score_entry(package, user=None):
    """
        Save featured package in the database.
    """
    if not check_exists(package):
        return
    # Prevent gaming the system
    if db.exists(config.REDIS_KEY_PACKAGE_TIMER % package):
        return
    timestamp = datetime.datetime.utcnow().strftime(config.TIMESTAMP)
    db.lpush(config.REDIS_KEY_PACKAGE_FEATURED_TIME % package, timestamp)
    db.set(config.REDIS_KEY_PACKAGE_TIMER % package, True)
    db.expire(config.REDIS_KEY_PACKAGE_TIMER % package,
        config.REDIS_EXPIRE_ONE_HOUR)
    db.incr(config.REDIS_KEY_PACKAGES_FEATURED_COUNT)
    db.lpush(config.REDIS_KEY_PACKAGES_ENTERED, package)
    score = db.zscore(config.REDIS_KEY_PACKAGES_FEATURED, package)
    if score is None:
        score = 0
    int(score)
    score += 1
    key = config.REDIS_KEY_PACKAGES_FEATURED
    try:
        db.zadd(key, score, package)
    except:  # XXX Try reverse order
        db.zadd(key, package, score)
    downloads = get_package_downloads(package)
    key = config.REDIS_KEY_PACKAGES_DOWNLOADED
    try:
        db.zadd(key, downloads, package)
    except:
        db.zadd(key, package, downloads)
    if user is not None:  # Per user stats
        db.incr(config.REDIS_KEY_USER_PACKAGE_COUNT % (user, package))
        db.lpush(config.REDIS_KEY_PACKAGES_ENTERED_USER % user, package)
        count = db.get(config.REDIS_KEY_USER_PACKAGE_COUNT % (user,
            package))
        key = config.REDIS_KEY_PACKAGES_FEATURED_USER
        try:
            db.zadd(key % user, count, package)
        except:  # XXX Try reverse order
            db.zadd(key % user, package, count)
        db.lpush(config.REDIS_KEY_USERS_ENTERED, user)
        packages = len(db.zrange(
            config.REDIS_KEY_PACKAGES_FEATURED_USER % user, 0, -1))
        key = config.REDIS_KEY_USERS_FEATURED
        try:
            db.zadd(key, packages, user)
        except:  # XXX Try reverse order
            db.zadd(key, user, packages)
        try:
            send_tweet("%s featured by %s %s/package/%s #python" % (
                package,
                user,
                config.PYTHON_PACKAGES_URL,
                package.lower(),
                )
            )
        except:
            # XXX TwitterError
            pass
        db.lpush(config.REDIS_KEY_PACKAGE_FEATURED_BY % package, user)
    else:
        db.lpush(config.REDIS_KEY_PACKAGE_FEATURED_BY % package, 'anonymous')


def score_release(package, user=None):
    """
        Save released package in the database.
    """
    timestamp = datetime.datetime.utcnow().strftime(config.TIMESTAMP)
    db.lpush(config.REDIS_KEY_PACKAGE_RELEASED_TIME % package, timestamp)
    db.incr(config.REDIS_KEY_PACKAGES_RELEASED_COUNT)
    db.lpush(config.REDIS_KEY_RELEASES_ENTERED, package)
    score = db.zscore(config.REDIS_KEY_RELEASES_FEATURED, package)
    if score is None:
        score = 0
    int(score)
    score += 1
    key = config.REDIS_KEY_RELEASES_FEATURED
    try:
        db.zadd(key, score, package)
    except:  # XXX Try reverse order
        db.zadd(key, package, score)
    db.incr(config.REDIS_KEY_USER_RELEASE_COUNT % (user, package))
    db.lpush(config.REDIS_KEY_RELEASES_ENTERED_USER % user, package)
    count = db.get(config.REDIS_KEY_USER_RELEASE_COUNT % (user, package))
    key = config.REDIS_KEY_PACKAGES_RELEASED_USER
    try:
        db.zadd(key % user, count, package)
    except:  # XXX Try reverse order
        db.zadd(key % user, package, count)


def send_mail(to=None, subject=None, body=None):
    """
        Send mail to beta users.
    """
    if body is None:
        body = 'Test'
    msg = MIMEText(str(body.encode('utf-8')))
    if subject is None:
        subject = 'Test'
    msg['Subject'] = subject
    if to is None:
        to = config.ADMIN_EMAIL
    msg['To'] = to
    msg['From'] = config.ADMIN_EMAIL
    try:
        s = smtplib.SMTP(config.GMAIL_HOST)
        s.starttls()
        s.login(config.GMAIL_USER, config.GMAIL_PASS)
        s.sendmail(config.ADMIN_EMAIL, [to], msg.as_string())
        s.quit()
    except:
        pass


def send_tweet(tweet):
    """
        Send tweet as @pythonpackages
    """
    return twitter.PostUpdate(tweet)


def set_avatar(user, avatar):
    """
        Save gravatar URL for user to the database.
    """
    try:
        db.set(config.REDIS_KEY_USER_AVATAR % user, avatar)
    except:
        # XXX No db
        pass


def set_email(user, email):
    """
        Save user email to the database.
    """
    try:
        db.set(config.REDIS_KEY_USER_EMAIL % user, email)
    except:
        # XXX No db
        pass


def set_logged_in(user):
    """
        Save signed in users to the database.
    """
    try:
        db.sadd('logged_in', user)  # logged in users
        db.sadd('site_users', user)  # all users ever
    except:
        pass
        # XXX No db
    return


def set_name(user, name):
    """
        Save user's full name to the database.
    """
    try:
        db.set(config.REDIS_KEY_USER_NAME % user, name)
    except:
        # XXX No db
        pass


def set_plan(user, plan):
    """
        Save selected plan for user to the database.
    """
    db.set(config.REDIS_KEY_USER_PLAN % user, plan)


def set_slots(user):
    """
        Save selected slots for user to the database.
    """
    if not db.exists(config.REDIS_KEY_USER_SLOTNUM_ORG % user):
        db.set(config.REDIS_KEY_USER_SLOTNUM_ORG % user, 0)
    if not db.exists(config.REDIS_KEY_USER_SLOTNUM_PACKAGE % user):
        db.set(config.REDIS_KEY_USER_SLOTNUM_PACKAGE % user, 1)
    # Stripe
    if not db.exists(config.REDIS_KEY_USER_SLOTMAX_ORG % user):
        db.set(config.REDIS_KEY_USER_SLOTMAX_ORG % user, 0)
    if not db.exists(config.REDIS_KEY_USER_SLOTMAX_PACKAGE % user):
        db.set(config.REDIS_KEY_USER_SLOTMAX_PACKAGE % user, 1)


def set_token(userid, token):
    """
        Save GitHub token for user to the database.
    """
    if token is not None:
        db.set(config.REDIS_KEY_USER_GITHUB_OAUTH_TOKEN % userid, token)


def trove_lookup(classifier):
    """
        Return pretty name for trove.
    """
    for choice in trove.choices:
        if choice[0] == classifier:
            return choice[1]


def validate_package(node, value):
    """
        Custom colander validator to check for valid package.
    """
    if not valid_package.match(value):
        raise colander.Invalid(node, '%r is not a valid package name' % value)


def write_tree(package, tree=None, token=None, user=None, alias=None,
    tempdir=None):
    """
        Write tree full o data
    """
    if tempdir is None:
        tempdir = os.path.abspath(tempfile.mkdtemp(prefix='clone-'))
    if alias is None:
        package_dir = '%s/%s' % (tempdir, package)
    else:
        package_dir = '%s/%s' % (tempdir, alias)
    os.mkdir(package_dir)
    if tree is not None:
        tree = tree['tree']
    for item in tree:
        path = item['path']
        if item['type'] == 'tree':
            os.mkdir('%s/%s' % (package_dir, path))
        else:
            outfile = open('%s/%s' % (package_dir, path), 'wb')
            key = item['sha']
            data = get_blob(package, key=key, token=token, user=user)
            outfile.write(data)
    return tempdir
