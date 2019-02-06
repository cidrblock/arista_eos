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
import json

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.common.providers import register_provider
from ansible.module_utils.network.eos.providers.cli.base import EosCliProvider


@register_provider('eos', 'eos_l3_interfaces')
class Provider(EosCliProvider):

    def render(self):
        commands = list()
        safe_list = list()

        operation = self.get_value('operation')
        config = self.get_value('config')

        collection = self.get_resource()
        interfaces = [c['name'] for c in collection]

        if operation == 'delete':
            if config:
                for item in config:
                    commands.extend([
                        'interface %s' % item['name'],
                        'no ip address',
                        'exit'
                    ])
            else:
                resp = self._negate_config(collection=collection)
                if resp:
                    commands.extend(resp)

        elif operation in ('override', 'replace'):
            safe_list = list()

            for item in config:
                context_commands = list()

                name = item['name']

                context = 'interface %s' % name
                safe_list.append(name)

                resp = self.render_item(item, None)
                if resp:
                    context_commands.append(context)
                    context_commands.append('no ip address')
                    context_commands.extend(to_list(resp))
                    context_commands.append('exit')

                commands.extend(context_commands)

            if operation == 'override':
                configobj = self.load_config(indent=3)
                resp = self._negate_config(safe_list=safe_list)
                if resp:
                    commands.extend(resp)

        elif operation == 'merge':
            for item in config:
                context_commands = list()

                name = item['name']
                obj = self.get_item(name)

                resp = self.render_item(item, obj)

                if obj is None or resp:
                    context_commands.append('interface %s' % name)

                if resp:
                    context_commands.extend(to_list(resp))

                if context_commands:
                    context_commands.append('exit')

                commands.extend(context_commands)

        return commands

    def render_item(self, item, obj=None):
        commands = list()
        for key, value in iteritems(item):
            if value is not None:
                meth = getattr(self, '_set_%s' % key, None)
                if meth:
                    resp = meth(item, obj)
                    if resp:
                        commands.extend(to_list(resp))
        return commands

    def get_item(self, name):
        for item in self.get_resource():
            if item['name' ] == name:
                return item

    def get_resource(self):
        collection = list()
        output = self.cli('show ip interface | json')

        for key, value in iteritems(output['interfaces']):
            collection.append({
                'name': key,
                'ipv4': {
                    'address': value['interfaceAddress']['primaryIp']['address'],
                    'masklen': value['interfaceAddress']['primaryIp']['maskLen']
                }
            })

        return collection

    def _negate_config(self, collection=None, safe_list=None):
        commands = list()
        safe_list = safe_list or list()

        if not collection:
            collection = self.get_resource()

        assert isinstance(collection, list)
        names = [c['name'] for c in collection]

        for item in set(names).difference(safe_list):
            if not item.lower().startswith('ma'):
                commands.extend([
                    'interface %s' % item,
                    'no ip address',
                    'exit'
                ])

        return commands

    def _set_ipv4(self, item, obj):
        if not obj:
            return 'ip address %s/%s' % (item['ipv4']['address'], item['ipv4']['masklen'])

        elif item['ipv4']['address'] != obj['ipv4']['address'] or \
             item['ipv4']['masklen'] != obj['ipv4']['masklen']:
            return 'ip address %s/%s' % (item['ipv4']['address'], item['ipv4']['masklen'])
