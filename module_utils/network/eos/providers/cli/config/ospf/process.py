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


@register_provider('eos', 'eos_ospf_processes')
class Provider(EosCliProvider):
    """ Arista EOS system object
    """

    def render(self):
        commands = list()

        operation = self.get_value('operation')
        config = self.get_value('config')
        resource = self.get_resource()

        self.display.append('configuring global ospf processes')

        if operation == 'delete':
            if resource:
                commands.append('no router ospf %s' % resource['process_id'])

        elif operation in ('merge', 'replace'):
            process_id = resource.get('process_id')

            if operation == 'replace':
                resource = None

            for key, value in iteritems(self.get_value('config')):
                meth = getattr(self, '_set_%s' % key, None)
                if meth:
                    resp = meth(resource)
                    if resp:
                        commands.extend(to_list(resp))

            if commands:
                commands.insert(0, 'router ospf %s' % self.get_value('config.process_id'))
                if operation == 'replace' and process_id:
                    commands.insert(0, 'no router ospf %s' % process_id)
                commands.append('exit')

        return commands

    def get_resource(self):
        obj = {}

        config_text = self.cli('show running-config | section router ospf')

        for item in self.get_value('config'):
            getter = getattr(self, '_get_%s' % item, None)
            if getter:
                obj[item] = getter(config_text)

        return obj

    def _get_process_id(self, config_text):
        match = re.search(r'router ospf (\d+)', config_text, re.M)
        return int(match.group(1)) if match else None

    def _get_router_id(self, config_text):
        match = re.search(r'router-id (.+)', config_text, re.M)
        return match.group(1) if match else None

    def _set_router_id(self, resource):
        router_id = self.get_value('config.router_id')
        if not resource or router_id != resource['router_id']:
            self.display.append('- setting ospf router-id to %s' % router_id)
            return 'router-id %s' % router_id

    def _get_networks(self, config_text):
        collection = list()
        matches = re.findall(r'network (.+) area (.+)', config_text, re.M)
        for network, area in matches:
            collection.append({'network': network, 'area': area})
        return collection

    def _set_networks(self, resource):
        commands = list()

        cmd = 'network {network} area {area}'
        nocmd = 'no %s' % cmd

        if resource:
            network_set = set(tuple(x.items()) for x in self.get_value('config.networks'))
            resource_set = set(tuple(x.items()) for x in resource['networks'])

            # deletes
            for item in resource_set.difference(network_set):
                item = dict((k, v) for k, v in item)
                commands.append(nocmd.format(**item))
                self.display.append('- removing network {network}, area {area} from ospf'.format(**item))

            # adds
            for item in network_set.difference(resource_set):
                item = dict((k, v) for k, v in item)
                commands.append(cmd.format(**item))
                self.display.append('- adding network {network}, area {area} to ospf'.format(**item))

        else:
            for item in self.get_value('config.networks'):
                commands.append(cmd.format(**item))
                self.display.append('- adding network {network}, area {area} to ospf'.format(**item))

        return commands




