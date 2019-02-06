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


@register_provider('eos', 'eos_system')
class Provider(EosCliProvider):
    """ Arista EOS system object
    """

    def render(self):
        commands = list()
        operation = self.get_value('operation')

        self.display.append('checking system resource configuration values')

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

    def _get_hostname(self, config_text):
        match = re.search(r'^hostname (.+)', config_text, re.M)
        return match.group(1) if match else None

    def _get_hostname(self, config_text):
        match = re.search(r'^hostname (.+)', config_text, re.M)
        return match.group(1) if match else None

    def _set_hostname(self, obj):
        if not obj or obj['hostname'] != self.get_value('config.hostname'):
            self.display.append('- setting system hostname to {hostname}'.format(**obj))
            return 'hostname %s' % self.get_value('config.hostname')

    def _del_hostname(self, obj):
        if obj['hostname']:
            return 'no hostname %s' % self.get_value('config.hostname')

    def _get_domain_name(self, config_text):
        match = re.search(r'ip domain-name (.+)', config_text, re.M)
        return match.group(1) if match else None

    def _set_domain_name(self, obj):
        if not obj or obj['domain_name'] != self.get_value('config.domain_name'):
            self.display.append('- setting system domain-name to {hostname}'.format(**obj))
            return 'ip domain-name %s' % self.get_value('config.domain_name')

    def _del_domain_name(self, obj):
        if obj['domain_name']:
            return 'no ip domain-name %s' % self.get_value('config.domain_name')

    def _get_domain_name(self, config_text):
        match = re.search(r'ip domain-name (.+)', config_text, re.M)
        return match.group(1) if match else None
