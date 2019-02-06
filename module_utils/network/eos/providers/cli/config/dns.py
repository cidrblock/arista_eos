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
import re

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.common.providers import register_provider
from ansible.module_utils.network.eos.providers.cli.base import EosCliProvider


@register_provider('eos', 'eos_dns')
class Provider(EosCliProvider):

    def render(self):
        commands = list()
        operation = self.get_value('operation')

        self.display.append('checking dns resource configuration values')

        if operation in ('merge', 'delete'):
            obj = self.get_resource()
        else:
            obj = {}
            for key in self.get_value('config'):
                obj[key] = None


        for key, value in iteritems(self.get_value('config')):
            if operation == 'delete':
                meth = getattr(self, '_del_%s' % key, None)
            elif value is not None:
                meth = getattr(self, '_set_%s' % key, None)
            else:
                meth = None

            if meth:
                resp = meth(obj)
                if resp:
                    commands.extend(to_list(resp))

        return commands

    def get_resource(self):
        obj = {}

        configobj = self.load_config(indent=3)
        config_text = configobj.config_text

        for meth in dir(self):
            if meth.startswith('_get_'):
                getter = getattr(self, meth)
                if getter:
                    key = re.match('_get_(.+)', meth).group(1)
                    obj[key] = getter(config_text)

        return obj

    def _get_name_servers(self, config_text):
        return re.findall(r'ip name-server vrf \S+ (\S+)', config_text, re.M)

    def _set_name_servers(self, obj):
        commands = list()

        current = obj['name_servers'] or list()
        desired = self.get_value('config.name_servers')

        for item in set(current).difference(desired):
            commands.append('no ip name-server %s' % item)

        for item in set(desired).difference(current):
            commands.append('ip name-server %s' % item)

        return commands

    def _del_name_servers(self, obj):
        commands = list()
        for item in obj['name_servers']:
            commands.append('no ip name-server %s' % item)
        return commands

    def _get_lookup_source(self, config_text):
        match = re.search(r'ip domain lookup source-interface (.+)', config_text, re.M)
        return match.group(1) if match else None

    def _set_lookup_source(self, obj):
        if not obj or obj['lookup_source'] != self.get_value('config.lookup_source'):
            return 'ip domain lookup source-interface %s' % self.get_value('config.lookup_source')

    def _del_lookup_source(self, obj):
        if obj['lookup_source']:
            return 'no domain lookup source-interface %s' % self.get_value('config.lookup_source')

    def _get_domain_search(self, config_text):
        return re.findall(r'ip domain-list (.+)', config_text, re.M)

    def _set_domain_search(self, obj):
        commands = list()

        current = obj['domain_search'] or list()
        desired = self.get_value('config.domain_search')

        for item in set(desired).difference(current):
            commands.append('ip domain-search %s' % item)

        for item in set(current).difference(desired):
            commands.append('no ip domain-search %s' % item)

        return commands

    def _del_domain_search(self, obj):
        commands = list()
        for item in obj['domain_search']:
            commands.append('no ip domain-search %s' % item)
        return commands
