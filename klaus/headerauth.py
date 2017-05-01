import os
import yaml

from fnmatch import fnmatch
from klaus.auth import BaseAuth, BaseAuthCache, FailAllCache, register_authorizer


class HeaderAuthCache(BaseAuthCache):
    def __init__(self, repos):
        self.repos = set(repos)
        self.patterns = [r for r in repos if '*' in r]

    def can_view(self, repo):
        for pattern in self.patterns:
            if fnmatch(repo, pattern):
                return True
        return repo in self.repos

class HeaderAuth(BaseAuth):
    def __init__(self, config_path):
        with open(config_path, 'rb') as f:
            config = yaml.load(f)
        self.header_name = config['username_header']
        self.auth_map = config['auth']

    def get_cache(self, request):
        user = request.headers.get(self.header_name)
        if user in self.auth_map:
            return HeaderAuthCache(self.auth_map[user])
        else:
            return FailAllCache()

    def current_user(self, request):
        return request.headers.get(self.header_name)


def make_headerauth():
    config_path = os.environ.get('KLAUS_HEADER_AUTH_CONFIG_PATH')
    if config_path is None:
        raise ValueError('KLAUS_HEADER_AUTH_CONFIG_PATH is not set!')
    return HeaderAuth(config_path)


register_authorizer('header', make_headerauth)
