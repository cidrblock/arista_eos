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


@register_provider('eos', 'eos_interfaces')
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
                    name = item['name']
                    if name in interfaces:
                        if name.lower().startswith('et'):
                            commands.append('default interface %s' % name)
                        elif not name.lower().startswith('ma'):
                            commands.append('no interface %s' % name)
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
                    context_commands.extend(to_list(resp))
                    context_commands.append('exit')

                context_commands.insert(0, 'no %s' % context)
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
        output = self.cli('show interfaces | json')

        for key, value in iteritems(output['interfaces']):
            collection.append({
                'name': key,
                'description': value['description'],
                'enabled': value['interfaceStatus'] != 'disabled'
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
            if item.lower().startswith('et'):
                commands.append('default interface %s' % item)
            elif not item.lower().startswith('ma'):
                commands.append('no interface %s' % item)

        return commands

    def _set_description(self, item, obj):
        if not obj or item['description'] != obj.get('description'):
            return 'description %s' % item['description']

    def _set_enabled(self, item, obj):
        if not obj or item['enabled'] != obj.get('enabled'):
            return 'no shutdown' if item['enabled'] is True else 'shutdown'
