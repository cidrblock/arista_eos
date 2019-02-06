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
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.common import providers
from ansible.module_utils._text import to_text


class NetworkModule(AnsibleModule):

    fail_on_missing_provider = True

    def __init__(self, module_config, connection=None):
        assert isinstance(module_config, dict)

        if 'supports_check_mode' not in module_config:
            module_config['supports_check_mode'] = True

        super(NetworkModule, self).__init__(**module_config)

        if connection is None:
            connection = Connection(self._socket_path)

        self.connection = connection

    @property
    def provider(self):
        if not hasattr(self, '_provider'):
            try:
                capabilities = self.from_json(self.connection.get_capabilities())
                network_os = capabilities['device_info']['network_os']
                network_api = capabilities['network_api']
            except:
                raise ValueError('unable to determine connection type')

            if network_api == 'cliconf':
                connection_type = 'network_cli'
            elif network_api == 'netconf':
                connection_type = 'netconf'
            else:
                raise ValueError('unsupported network api %s' % network_api)

            cls = providers.get(network_os, self._name, connection_type)

            if not cls:
                msg = 'unable to find suitable provider for network os %s' % network_os
                if self.fail_on_missing_provider:
                    self.fail_json(msg=msg)
                else:
                    self.warn(msg)

            obj = cls(self.connection)
            setattr(self, '_provider', obj)

        return getattr(self, '_provider')


class NetworkConfigModule(NetworkModule):

    def run(self):
        try:
            self.log('invoking provider %s' % type(self.provider))
            result = {'changed': True}

            response = self.provider.edit_resource(self.params, self.check_mode)
            result.update(response)
            #result.update({'commands': commands})

            for msg in self.provider.warnings:
                self.warn(msg)

            for msg in self.provider.messages:
                self.log(msg)

            result['display'] = self.provider.display

            resource_name = '_'.join(self._name.split('_')[1:])
            resource = {'config': self.provider.get_resource()}

            result['ansible_facts'] = {resource_name: resource}

            if self.provider.changed in (True, False):
                result['changed'] = self.provider.changed
            elif self.provider.changed is None:
                self.warn('unable to determine if a change was made due to the '
                          'provider changed flag set to None')
            else:
                self.fail_json(msg='invalid value set on provider for changed.'
                                   'expected type <bool>, got %s' % type(self.provider.changed))

            self.log('finished provider %s' % type(self.provider))
            return result

        except providers.ProviderError as exc:
            kwargs = {'msg': exc.kwargs.pop('msg', 'Unknown provider error')}
            if self._verbosity > 2:
                kwargs['provider'] = {
                    'error': exc.kwargs,
                    'device': {
                        'network_os': self.provider.capabilities['device_info']['network_os'],
                        'software_version': self.provider.capabilities['device_info']['network_os_version'],
                        'network_api': self.provider.capabilities['network_api']
                    }
                }
            self.fail_json(**kwargs)

        except Exception as exc:
            self.fail_json(msg=to_text(exc))

class NetworkFactsModule(NetworkModule):

    def run(self):
        try:
            result = {'changed': False}
            for msg in self.provider.warnings:
                self.warn(msg)

            facts = {}
            for item in self.provider.resources:
                facts[item] = self.provider.get_resource(item)

            result['ansible_facts'] = {'ansible_network': resource}

            return result

        except providers.ProviderError as exc:
            kwargs = {'msg': exc.kwargs.pop('msg', 'Unknown provider error')}
            if self._verbosity > 2:
                kwargs['provider'] = {
                    'error': exc.kwargs,
                    'device': {
                        'network_os': self.provider.capabilities['device_info']['network_os'],
                        'software_version': self.provider.capabilities['device_info']['network_os_version'],
                        'network_api': self.provider.capabilities['network_api']
                    }
                }
            self.fail_json(**kwargs)

        except Exception as exc:
            self.fail_json(msg=to_text(exc))




