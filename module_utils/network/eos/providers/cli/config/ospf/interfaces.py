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
# are permitted provided that the following conditions are met: #
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
import re

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.common.providers import register_provider
from ansible.module_utils.network.eos.providers.cli.base import EosCliProvider


@register_provider('eos', 'eos_ospf_interfaces')
class Provider(EosCliProvider):

    def render(self):
        commands = list()

        operation = self.get_value('operation')
        config = self.get_value('config')

        collection = self.get_resource()

        if operation == 'delete':
            for resource in collection:
                context_commands = list()

                for key, value in iteritems(resource):
                    if value is not None:
                        deleter = getattr(self, '_del_%s' % key, None)
                        if deleter:
                            resp = deleter(resource)
                            if resp:
                                context_commands.extend(to_list(resp))

                if context_commands:
                    commands.append('interface %s' % resource['name'])
                    commands.extend(context_commands)
                    commands.append('exit')

        elif operation == 'merge':
            for desired in config:
                context_commands = list()
                current = self._match_resource(desired['name'])

                for key, value in iteritems(desired):
                    if value is not None:
                        setter = getattr(self, '_set_%s' % key, None)
                        if setter:
                            resp = setter(desired, current)
                            if resp:
                                context_commands.extend(to_list(resp))

                if context_commands:
                    commands.append('interface %s' % desired['name'])
                    commands.extend(context_commands)
                    commands.append('exit')

        elif operation in ('replace', 'override'):
            safe_list = list()
            for desired in config:
                self.display.append('configuring ospf interface {name}'.format(**desired))
                safe_list.append(desired['name'])
                commands.append('interface %s' % desired['name'])
                for key, value in iteritems(desired):
                    if value is not None:
                        setter = getattr(self, '_set_%s' % key, None)
                        if setter:
                            resp = setter(desired)
                            commands.extend(to_list(resp))
                commands.append('exit')

            if operation == 'override':
                resp = self._negate_config(safe_list=safe_list)
                if resp:
                    commands.extend(resp)

        return commands

    def _match_resource(self, name):
        for item in self.get_resource():
            if item['name'] == name:
                return item

    def get_resource(self):
        collection = list()

        output = self.cli('show running-config')
        configobj = NetworkConfig(indent=3, contents=output)

        interfaces = re.findall(r"^interface (.+)", output, re.M)

        for name in interfaces:
            obj = {}
            config_text = configobj.get_block_config(['interface %s' % name])
            for key in self.get_value('config')[0]:
                getter = getattr(self, '_get_%s' % key, None)
                if getter:
                    resp = getter(config_text)
                    if resp:
                        obj[key] = resp
                else:
                    obj[key] = None
            obj['state'] = 'present' if 'ip ospf' in config_text else 'absent'
            collection.append(obj)

        return collection

    def _negate_config(self, collection=None, safe_list=None):
        commands = list()
        safe_list = safe_list or list()

        safe_list.append('Management1')

        if not collection:
            collection = self.get_resource()

        for item in collection:
            if item['name'] not in safe_list and item['state'] == 'present':
                context_commands = list()

                for key, value in iteritems(item):
                    if value is not None:
                        deleter = getattr(self, '_del_%s' % key, None)
                        if deleter:
                            resp = deleter(item)
                            if resp:
                                context_commands.extend(to_list(resp))

                if context_commands:
                    commands.append('interface %s' % item['name'])
                    commands.extend(context_commands)
                    commands.append('exit')

        return commands

    def _get_name(self, config_text):
        match = re.match(r'^interface (.+)', config_text, re.M)
        return match.group(1)

    def _get_enabled(self, config_text):
        return 'ip ospf shutdown' not in config_text

    def _set_enabled(self, desired, current=None):
        if not current or current['enabled'] != desired['enabled']:
            if desired['enabled'] is True:
                self.display.append('- setting ospf interface enabled to True')
                return 'no ip ospf shutdown'
            else:
                self.display.append('- setting ospf interface enabled to False')
                return 'ip ospf shutdown'

    def _del_enabled(self, current):
        return 'no ip ospf shutdown'

    def _get_cost(self, config_text):
        match = re.match(r'ip ospf cost (\d+)', config_text, re.M)
        return int(match.group(1)) if match else None

    def _set_cost(self, desired, current=None):
        if not current or current['cost'] != desired['cost']:
            self.display.append('- setting ospf interface cost to {cost}'.format(**desired))
            return 'ip ospf cost %s' % desired['cost']

    def _del_cost(self, current):
        return 'no ip ospf cost'
