import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


requires = [
    'Paste',  # *shrug*
    'deform',
    'deform_bootstrap',
    'docutils',
    'fortune',
    'pbs',
    'pycryptopp',
    'pypi.trashfinder',
    'pyramid',
    'pyramid_beaker',
    'pythonpackages-scaffolds',
    'python-twitter',
    'redis',
    'requests',
    'rq',
    'stripe',
    'vanity',
    'waitress',
    'yolk',
]

setup(name='vanity_app',
      version='0.0.0',
      description='vanity_app',
      long_description='',
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="vanity_app",
      entry_points="""\
      [paste.app_factory]
      main=vanity_app:main
      """,
      paster_plugins=['pyramid'],
      )
