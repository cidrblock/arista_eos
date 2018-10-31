from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.arista_eos.config import ConfigBase

class BgpNetwork(ConfigBase):

    argument_spec = {
        'network': dict(required=True),
        'route_map': dict(),
        'state': dict(choices=['present', 'absent'], default='present')
    }

    identifier = ('network', )

    def render(self, config=None):
        cmd = 'network %s' % self.network
        if self.route_map:
            cmd += ' route-map %s' % self.route_map

        if self.state == 'absent':
            if not config or cmd in config:
                return 'no %s' % cmd

        elif self.state in ('present', None):
            if not config or cmd not in config:
                return cmd
