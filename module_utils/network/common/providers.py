#
# This code is part of Ansible, but is an independent component.
#
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Red Hat, Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import json

from threading import RLock

from ansible.module_utils.six import itervalues
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.common.config import NetworkConfig


_registered_providers = {}
_provider_lock = RLock()


class ProviderError(Exception):

    def __init__(self, message, **kwargs):
        super(ProviderError, self).__init__(message)
        if 'msg' not in kwargs:
            kwargs['msg'] = message
        self.kwargs = kwargs


def register_provider(network_os, module_name):
    def wrapper(cls):
        _provider_lock.acquire()
        try:
            if network_os not in _registered_providers:
                _registered_providers[network_os] = {}
            for ct in cls.supported_connections:
                if ct not in _registered_providers[network_os]:
                    _registered_providers[network_os][ct] = {}
            for item in to_list(module_name):
                for entry in itervalues(_registered_providers[network_os]):
                    entry[item] = cls
        finally:
            _provider_lock.release()
        return cls
    return wrapper


def get(network_os, module_name, connection_type):
    network_os_providers = _registered_providers.get(network_os)
    if network_os_providers is None:
        raise ValueError('unable to find a suitable provider for this module')
    if connection_type not in network_os_providers:
        raise ValueError('provider does not support this connection type')
    elif module_name not in network_os_providers[connection_type]:
        raise ValueError('could not find a suitable provider for this module')
    return network_os_providers[connection_type][module_name]



class ProviderBase(object):

    supported_connections = ()

    def __init__(self, connection):
        self.connection = connection
        self.params = None
        self.check_mode = None
        self.warnings = list()
        self.messages = list()
        self.display = list()
        self.changed = None

    @property
    def capabilities(self):
        if not hasattr(self, '_capabilities'):
            resp = json.loads(self.connection.get_capabilities())
            setattr(self, '_capabilities', resp)
        return getattr(self, '_capabilities')

    def warn(self, msg):
        self.warnings.append(msg)

    def log(self, msg):
        self.messages.append(msg)

    def display(self, msg):
        self.display.append(msg)

    def get_value(self, path):
        params = self.params.copy()
        for key in path.split('.'):
            params = params[key]
        return params

    def get_resource(self):
        raise NotImplementedError(self.__class__.__name__)

    def edit_resource(self, params, check_mode=None):
        self.params = params
        self.check_mode = check_mode


class CliProvider(ProviderBase):

    supported_connections = ('network_cli',)

    def __init__(self, connection):
        super(CliProvider, self).__init__(connection)
        self._configobj = None

    def load_config(self, indent=1):
        if self._configobj:
            return self._configobj
        else:
            self.log('calling get_config() on connection')
            config_text = self.connection.get_config()
            self._configobj = NetworkConfig(contents=config_text, indent=indent)
            return self._configobj

    def render(self):
        raise NotImplementedError(self.__class__.__name__)

    def cli(self, command):
        try:
            self.log("found cli command '%s' in cache" % command)
            if not hasattr(self, '_command_output'):
                setattr(self, '_command_output', {})
            return self._command_output[command]
        except KeyError:
            self.log('executing cli command: %s' % command)
            out = self.connection.get(command)
            try:
                out = json.loads(out)
            except ValueError:
                pass
            self._command_output[command] = out
            return out

    def edit_resource(self, params, check_mode=None):
        super(CliProvider, self).edit_resource(params, check_mode)

        response = dict()

        commands = self.render()
        response['commands'] = commands

        if commands and self.check_mode is False:
            resp = self.connection.edit_config(commands)
            response.update(resp)

        self.changed = bool(commands)
        return response
        #return commands


class NetconfProvider(ProviderBase):

    supported_connections = ('netconf',)

    def get_resource(self):
        pass

    def edit_resource(self):
        xml = self.render()
        if xml and self.check_mode is False:
            self.connection.edit_config(xml)

