from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.arista_eos.config import ConfigBase
from ansible.module_utils.arista_eos.config.bgp import get_bgp_as
from ansible.module_utils.arista_eos.config.bgp.neighbor import BgpNeighbor
from ansible.module_utils.arista_eos.config.bgp.redistribute import BgpRedistribute

class BgpAddressFamily(ConfigBase):

    argument_spec = {
        'name': dict(choices=['ipv4', 'ipv6', 'vpnv4'], required=True),
        'vrf': dict(),
        'neighbors': dict(type='list', elements='dict', options=BgpNeighbor.argument_spec),
        'redistribute': dict(type='list', elements='dict', options=BgpRedistribute.argument_spec),
        'state': dict(choices=['present', 'absent'], default='present')
    }

    identifier = ('name', )

    def render(self, config=None):
        commands = list()

        context = 'address-family %s' % self.name
        if self.vrf:
            context += ' vrf %s' % self.vrf

        if config:
            bgp_as = get_bgp_as(config)
            if bgp_as is not None:
                section = ['router bgp %s' % bgp_as, context]
                config = self.get_section(config, section)

        if self.state == 'absent':
            if context in config:
                commands.append('no %s' % context)

        if self.state == 'present':
            subcommands = list()
            for attr in self.argument_spec:
                if attr in self.values:
                    meth = getattr(self, '_set_%s' % attr, None)
                    if meth:
                        resp = meth(config)
                        if resp:
                            subcommands.extend(to_list(resp))

            if subcommands:
                commands = [context]
                commands.extend(subcommands)
                commands.append('exit-address-family')
            elif not config or context not in config:
                commands.extend([context, 'exit-address-family'])

        return commands

    def _set_neighbors(self, config=None):
        commands = list()
        for entry in self.neighbors:
            nbr = BgpNeighbor(**entry)
            resp = nbr.render(config)
            if resp:
                commands.extend(resp)
        return commands

    def _set_redistribute(self, config):
        commands = list()
        for entry in self.redistribute:
            redis = BgpRedistribute(**entry)
            resp = redis.render(config)
            if resp:
                commands.append(resp)
        return commands


