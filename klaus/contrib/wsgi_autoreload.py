from __future__ import print_function
import os
import time
import threading
import warnings
from io import open, StringIO

from klaus import make_app
from .app_args import get_args_from_env


# Shared state between poller and application wrapper
class _:
    #: the real WSGI app
    inner_app = None
    should_reload = True


def poll_for_changes(interval, dir):
    """
    Polls `dir` for changes every `interval` seconds and sets `should_reload`
    accordingly.
    """
    old_contents = os.listdir(dir)
    while 1:
        time.sleep(interval)
        if _.should_reload:
            # klaus application has not seen our change yet
            continue
        new_contents = os.listdir(dir)
        if new_contents != old_contents:
            # Directory contents changed => should_reload
            old_contents = new_contents
            _.should_reload = True


def find_git_repos(repos_root):
    all_repos = []
    for dirpath, dirnames, _ in os.walk(repos_root):
        for name in dirnames:
            fullpath = os.path.join(dirpath, name)
            headpath = os.path.join(fullpath, 'HEAD')
            if fullpath.endswith('.git'):
                if os.path.isfile(headpath):
                    all_repos.append(fullpath)
                    print("Found {0}".format(fullpath))
                else:
                    print("No HEAD in {0}!".format(fullpath))
    return all_repos


def make_autoreloading_app(repos_root, *args, **kwargs):
    def app(environ, start_response):
        if _.should_reload:
            # Refresh inner application with new repo list
            print("Reloading repository list...")
            authorizer = os.environ.get('KLAUS_AUTHORIZER')
            repo_hierarchy = os.environ.get('KLAUS_REPO_HIERARCHY')
            if repo_hierarchy == "y":
                _.inner_app = make_app(
                    find_git_repos(repos_root),
                    repos_root=repos_root,
                    authorizer=authorizer,
                    *args, **kwargs
                )
            else:
                _.inner_app = make_app(
                    [os.path.join(repos_root, x) for x in os.listdir(repos_root)],
                    authorizer=authorizer,
                    *args, **kwargs
                )
            _.should_reload = False
        return _.inner_app(environ, start_response)

    # Background thread that polls the directory for changes
    poller_thread = threading.Thread(target=(lambda: poll_for_changes(10, repos_root)))
    poller_thread.daemon = True
    poller_thread.start()

    return app


if 'KLAUS_REPOS' in os.environ:
    warnings.warn("use KLAUS_REPOS_ROOT instead of KLAUS_REPOS for the autoreloader apps", DeprecationWarning)

args, kwargs = get_args_from_env()
repos_root = os.environ.get('KLAUS_REPOS_ROOT') or os.environ['KLAUS_REPOS']
args = (repos_root,) + args[1:]

if kwargs['htdigest_file']:
    # Cache the contents of the htdigest file, the application will not read
    # the file like object until later when called.
    with open(kwargs['htdigest_file'], encoding='utf-8') as htdigest_file:
        kwargs['htdigest_file'] = StringIO(htdigest_file.read())

application = make_autoreloading_app(*args, **kwargs)
