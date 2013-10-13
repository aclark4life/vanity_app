# encoding: utf-8
import os

HERE = os.path.dirname(__file__)

# Hosted config files
BUILDOUT_USER = 'pythonpackages'
BUILDOUT_INDEX = open(os.path.join(HERE, 'templates', 'buildout.html')).read()
BUILDOUT_REPOS = (
    ('buildout-apache-modwsgi', 'apache-modwsgi'),
    ('buildout-bluebream', 'bluebream'),
    ('buildout-django', 'django'),
    ('buildout-jenkins', 'jenkins'),
    ('buildout-plone', 'plone'),
    ('buildout-plone-getpaid', 'plone-getpaid'),
    ('buildout-wordpress', 'wordpress'),
    ('buildout-zope2', 'zope2'),
)

# Redis
REDIS_EXPIRE_ONE_DAY = 86400
REDIS_EXPIRE_ONE_HOUR = 3600

# Assign redis key names to variable names (and in some cases, poorly
# chosen key names to better chosen variable names)
REDIS_KEY_BETA_USER = 'users:%s.%s'  # Hash (full_name, email_address,
                                     # github_username, classifiers)
REDIS_KEY_BETA_USERS = 'beta_users'  # Set
REDIS_KEY_NUM_PACKAGES_PYPI = 'num_packages_pypi'
REDIS_KEY_PACKAGE_DOWNLOADS = 'package:%s:downloads'
REDIS_KEY_PACKAGE_FEATURED_BY = 'package:%s:featured_by'  # List
REDIS_KEY_PACKAGE_FEATURED_TIME = 'package:%s:featured_time'  # List
REDIS_KEY_PACKAGE_METADATA = 'package:%s:metadata'
REDIS_KEY_PACKAGE_RELEASED_TIME = 'release:%s:featured_time'  # List
REDIS_KEY_PACKAGE_TIMER = 'package:%s:timer'
REDIS_KEY_PACKAGE_TRASH = 'package:%s:trash'
REDIS_KEY_PACKAGE_VERSION = 'package:%s:latest_version'
REDIS_KEY_PACKAGES_DOWNLOADED = 'recent_entries'  # Sorted set
REDIS_KEY_PACKAGES_ENTERED = 'entries'  # List
REDIS_KEY_PACKAGES_ENTERED_USER = 'user:%s:package_list'  # List
REDIS_KEY_PACKAGES_FEATURED = 'most_vain'  # Sorted set
REDIS_KEY_PACKAGES_FEATURED_COUNT = 'featured_count'
REDIS_KEY_PACKAGES_FEATURED_USER = 'user:%s:package_set'  # Sorted set
REDIS_KEY_PACKAGES_RELEASED_COUNT = 'released_count'
REDIS_KEY_PACKAGES_RELEASED_USER = 'user:%s:release_set'  # Sorted set
REDIS_KEY_RELEASES_ENTERED = 'releases'  # List
REDIS_KEY_RELEASES_ENTERED_USER = 'user:%s:release_list'  # List
REDIS_KEY_RELEASES_FEATURED = 'most_released'  # Sorted set
REDIS_KEY_TROVE_CLASSIFIER = 'trove:%s'
REDIS_KEY_TROVE_CLASSIFIERS_ENTERED = 'trove:list'
REDIS_KEY_TROVE_CLASSIFIERS_FEATURED = 'trove:set'
REDIS_KEY_USERS_ENTERED = 'users'  # List
REDIS_KEY_USERS_FEATURED = 'recent_users'  # Sorted set
REDIS_KEY_USERS_WHITELIST = 'users_whitelist'  # Set
REDIS_KEY_USER_AVATAR = 'user:%s:avatar'
REDIS_KEY_USER_CUSTOMER = 'user:%s:customer'
REDIS_KEY_USER_EMAIL = 'user:%s:email'
REDIS_KEY_USER_GITHUB_OAUTH_TOKEN = 'user:%s:token'
REDIS_KEY_USER_NAME = 'user:%s:name'
REDIS_KEY_USER_ORG_SELECTED = 'user:%s:org_selected'
REDIS_KEY_USER_ORGS_SELECTED = 'user:%s:orgs_selected'  # Hash
REDIS_KEY_USER_PACKAGE_SELECTED = 'user:%s:package_selected'
REDIS_KEY_USER_PACKAGES_SELECTED = 'user:%s:packages_selected'  # Hash
REDIS_KEY_USER_PACKAGE_COUNT = 'user:%s:package:%s'
REDIS_KEY_USER_PLAN = 'user:%s:plan'
REDIS_KEY_USER_RELEASE_COUNT = 'user:%s:release:%s'
REDIS_KEY_USER_PYPI_OAUTH_SECRET = 'user:%s:pypi_oauth_secret'  # PyPI oauth1
REDIS_KEY_USER_PYPI_OAUTH_TOKEN = 'user:%s:pypi_oauth_token'  # PyPI oauth1
REDIS_KEY_USER_SLOTMAX_ORG = 'user:%s:slotnum_org'  # For stripe
REDIS_KEY_USER_SLOTMAX_PACKAGE = 'user:%s:slotnum_package'  # For stripe
REDIS_KEY_USER_SLOTNUM_ORG = 'user:%s:org_slots'
REDIS_KEY_USER_SLOTNUM_PACKAGE = 'user:%s:package_slots'

# Github
if 'STAGING' in os.environ:
    GITHUB_SCOPES = 'delete_repo,repo'
else:
    GITHUB_SCOPES = 'repo'  # http://developer.github.com/v3/oauth/#scopes
if 'STAGING' in os.environ:
    GITHUB_CLIENT_ID = ''
    GITHUB_CLIENT_SECRET = ''
else:
    GITHUB_CLIENT_ID = ''
    GITHUB_CLIENT_SECRET = ''
GITHUB_URL = 'https://github.com'
GITHUB_URL_API = 'https://api.github.com'
GITHUB_URL_AUTH = (GITHUB_URL +
    '/login/oauth/authorize?client_id=%s&scope=%s' % (
    GITHUB_CLIENT_ID, GITHUB_SCOPES))
GITHUB_URL_ORG_INFO = GITHUB_URL_API + '/orgs/%s'
GITHUB_URL_ORG_REPO = GITHUB_URL_API + '/repos/%s/%s'
GITHUB_URL_ORG_REPOS = GITHUB_URL_API + '/orgs/%s/repos?per_page=100&page=%s'
GITHUB_URL_ORG_REPOS_NEW = GITHUB_URL_API + '/orgs/%s/repos?%s'
GITHUB_URL_REPOS_NEW = GITHUB_URL_API + '/user/repos?%s'
GITHUB_URL_REPOS_BLOB = (GITHUB_URL_API +
    '/repos/%s/%s/git/blobs/%s?%s')
GITHUB_URL_REPOS_BLOB_ANON = (GITHUB_URL_API +
    '/repos/%s/%s/git/blobs/%s')  # No qs needed
GITHUB_URL_REPOS_COMMITS = GITHUB_URL_API + '/repos/%s/%s/commits?%s'
GITHUB_URL_REPOS_DELETE = GITHUB_URL_API + '/repos/%s/%s?%s'
GITHUB_URL_REPOS_REFS = (GITHUB_URL_API +
    '/repos/%s/%s/git/refs?%s')
GITHUB_URL_REPOS_TAGS = (GITHUB_URL_API +
    '/repos/%s/%s/git/tags?%s')
GITHUB_URL_REPOS_TREE = (GITHUB_URL_API +
    '/repos/%s/%s/git/trees/%s?recursive=1?%s')
GITHUB_URL_REPOS_TREE_CREATE = (GITHUB_URL_API +
    '/repos/%s/%s/git/trees?%s')
GITHUB_URL_TOKEN = GITHUB_URL + '/login/oauth/access_token'
GITHUB_URL_USER = GITHUB_URL_API + '/user?%s'
GITHUB_URL_USER_ORGS = GITHUB_URL_API + '/user/orgs?%s'
GITHUB_URL_USER_REPO = GITHUB_URL_API + '/repos/%s/%s?%s'
GITHUB_URL_USER_REPOS = GITHUB_URL_API + '/user/repos?%s&per_page=100'

# GMail
GMAIL_HOST = 'smtp.gmail.com'
GMAIL_PASS = ''
GMAIL_USER = 'aclark@pythonpackages.com'

# Mail
MESSAGE = """
Hi %s,

%s

---
pythonpackages.com
"""

# Menu
MENU = """\
<div class="btn-group pull-right">
  <a class="btn dropdown-toggle login" data-toggle="dropdown" href="#">
    <img src="%s"> %s
    <span class="caret"></span>
  </a>
  <ul class="dropdown-menu">
    <li><a href="/dashboard"><i
        class="icon-user"></i> Dashboard</a></li>
    <li class="divider"></li>
    <li><a href="/logout"><i class="icon-off"></i> Sign out</a></li>
  </ul>
</div>
"""
MENU_SIGNIN = """\
<div class="btn-group pull-right">
    <a class="btn" href="%s">Sign in with GitHub</a>
</div>
"""

# Misc
ADMIN_EMAIL = 'pythonpackages.com <info@pythonpackages.com>'
COOKIE_PYPI = '_pp000'
COOKIE_GITHUB = '_pp001'
COOKIE_ENCRYPT = ''
COOKIE_VALIDATE = ''
CRATE_DOWNLOAD_URL = 'http://crate.io/api/v1/release/%s-%s/?format=json'
DEFAULT_ACTIVITY_LIMIT = 4
DEFAULT_LIMIT = 5
DEFAULT_TAB = 'downloaded'
DOCS = {
    'python.org': 'http://packages.python.org',
    'readthedocs.org': 'http://readthedocs.org/docs',
    'zope.org': 'http://docs.zope.org',
}
DOCUTILS_SETTINGS = {
    # Via https://svn.python.org/packages/trunk/pypi/description_utils.py
    'raw_enabled': 0,  # no raw HTML code
    'file_insertion_enabled': 0,  # no file/URL access
    'halt_level': 2,  # at warnings or errors, raise an exception
    'report_level': 5,  # never report problems with the reST code
}
FORTUNE_FILE = os.path.join(HERE, 'fortunes', 'fortunes')
MANAGE_PACKAGE_ACTIONS = (
    'add-slot-here',
    'run-test-suite',
    'tag-and-release',
    'test-installation',
    'upload-to-test-index',
)
METADATA_IGNORE = {
    'fields': (
        '_pypi_hidden',
        '_pypi_ordering',
        'classifiers',
        'name',
        'summary',
        'version'
    ),
    'values': (
        list(),
        None,
        str(),
        'UNKNOWN',
    )
}
PERMS = (
    'manage_dashboard',
    'manage_package',
    'manage_site',
)
PYTHON_PACKAGES_URL = 'http://pythonpackages.com'
TEST_USER_MAIL = 'aclark@aclark.net'
TEST_USER_NAME = 'Alex Clark'
TIMESTAMP = 'at %l:%M %p on %a %b %d %Y UTC'
USER_SLOTMAX_ORG = 0
USER_SLOTMAX_PACKAGE = 1

# Opencomparison
OPENCOMP_FRAMEWORKS = ('django', 'pyramid', 'plone')
OPENCOMP_SERVICE_URLS = (
    'http://%s.opencomparison.org',
    'http://%s.opencomparison.org/api/v1/package/%s',
    )

# Packaging
MANIFEST_IN = """\
include *
recursive-include docs *
recursive-include %s *
"""
PASTER_CONFIG = """\
[pastescript]
author = %s
author_email = %s
url = %s
"""

# Paster
PASTER_TEMPLATE_CHOICES = (
    ('basic_package', 'Basic package for a Python library'),
    ('django_app', 'Basic package for a Django app'),
    ('alchemy',
        'Basic package for Pyramid SQLAlchemy project using url dispatch'),
    ('starter', 'Basic package for Pyramid starter project'),
    ('zodb', 'Basic package for Pyramid ZODB project using traversal'),
    ('basic_namespace', 'Namespace package for a Python library'),
    ('basic_zope', 'Namespace package for a Zope 2 product'),
    ('plone', 'Namespace package for a Plone add-on'),
    ('plone2_theme', 'Namespace package for a Plone 2.1 theme'),
    ('plone2.5_theme', 'Namespace package for a Plone 2.5 theme'),
    ('plone3_theme', 'Namespace package for a Plone 3 theme'),
    ('plone_theme', 'Namespace package for a Plone 4 theme'),
    ('plone_pas', 'Namespace package for a Plone PAS plugin'),
    ('kss_plugin', 'Namespace package for a Plone KSS plugin'),
    ('archetype', 'Namespace package for Plone Archetypes content'),
    ('dexterity', 'Namespace package for Plone Dexterity content'),
    ('plone3_portlet', 'Nested namespace package for a Plone 3 portlet'),
    ('recipe', 'Nested namespace package for a Buildout recipe'),
    ('plone_app', 'Nested namespace package for a Plone add-on'),
    ('nested_namespace', 'Nested namespace package for a Python library'),
)

# Plans
PLANS_CHOICES = (
    ('free', u'Free Plan — $0 USD/Month — 1 Package Slot'),
    ('hobbyist', u'Hobbyist Plan — $7 USD/Month — 1 Organization Slot and \
        3 Package Slots'),
    ('semi-pro', u'Semi-pro Plan — $15 USD/Month — 2 Organization Slots \
        and 6 Package Slots'),
    ('professional', u'Professional Plan — $31 USD/Month — 4 Organization \
        Slots and 12 Package Slots'),
    ('corporate', u'Corporate Plan — $184 USD/Month — 8 Organization slots \
        and 144 Package Slots'),
    ('game-changer', u'Game Changer Plan — $400 USD/Month — Unlimited \
        Organization and Package Slots'),
)
PLANS_DATA = {
    # name  id cents orgslots packageslots
    'free': (0, '0', 0, 1),
    'hobbyist': (1, '700', 1, 3),
    'semi-pro': (2, '1500', 2, 6),
    'professional': (3, '3100', 4, 12),
    'corporate': (4, '18400', 8, 144),
    'game-changer': (5, '40000', 100, 1000),
}
# .pypirc
PYPIRC = """\
[distutils]
index-servers =
    pypi
[pypi]
username:%s
password:%s
"""
PYPIRC_TEST = """\
[distutils]
index-servers =
    other
    pypi
[other]
repository: http://index.pythonpackages.com
username:%s
password:%s
[pypi]
username:%s
password:%s
"""
# PyPI
PYPI_URL = 'http://pypi.python.org/pypi'
PYPI_OAUTH_CONSUMER_KEY = u'ingsssogen'
PYPI_OAUTH_CONSUMER_SECRET = u'ratolossit'
PYPI_URL_OAUTH_ACCESS_TOKEN = 'https://pypi.python.org/oauth/access_token'
PYPI_URL_OAUTH_ADD_RELEASE = 'https://pypi.python.org/oauth/add_release'
PYPI_URL_OAUTH_AUTHORIZE = ('https://pypi.python.org/oauth/authorise'
    '?oauth_token=%s&oauth_callback=%s')
if 'STAGING' in os.environ:
    PYPI_URL_OAUTH_CALLBACK = 'https://test.pythonpackages.com/login'
else:
    PYPI_URL_OAUTH_CALLBACK = 'https://pythonpackages.com/login'
PYPI_URL_OAUTH_REQUEST_TOKEN = (
    'https://pypi.python.org/oauth/request_token')
PYPI_URL_OAUTH_TEST = 'https://pypi.python.org/oauth/test'
PYPI_URL_OAUTH_UPLOAD = 'https://pypi.python.org/oauth/upload'

# Stripe
if 'STAGING' in os.environ:
    STRIPE_API_KEY = "" # Testing
else:
    STRIPE_API_KEY = "" # Live

# Twitter
TWITTER_ACCESS_TOKEN = ''
TWITTER_ACCESS_SECRET = ''
TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''
