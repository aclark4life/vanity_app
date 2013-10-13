import os
import sys
import redis
import readline
import rlcompleter
import urlparse
readline.parse_and_bind('tab: complete')


if 'REDISTOGO_URL' in os.environ:
    urlparse.uses_netloc.append('redis')
    url = urlparse.urlparse(os.environ['REDISTOGO_URL'])
    db = redis.Redis(host=url.hostname, port=url.port, db=0, password=url.password)
else:
    db = redis.Redis()


_interactive = True
if len(sys.argv) > 1:
    _options, _args = __import__("getopt").getopt(sys.argv[1:], 'ic:m:')
    _interactive = False
    for (_opt, _val) in _options:
        if _opt == '-i':
            _interactive = True
        elif _opt == '-c':
            exec _val
        elif _opt == '-m':
            sys.argv[1:] = _args
            _args = []
            __import__("runpy").run_module(
                 _val, {}, "__main__", alter_sys=True)

    if _args:
        sys.argv[:] = _args
        __file__ = _args[0]
        del _options, _args
        execfile(__file__)

if _interactive:
    del _interactive
    __import__("code").interact(banner="", local=globals())

