from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.arista_eos.config import ConfigBase

class BgpNeighbor(ConfigBase):

    argument_spec = {
        'neighbor': dict(required=True),
        'activate': dict(type='bool'),
        'description': dict(),
        'enabled': dict(type='bool'),
        'remote_as': dict(type='int'),
        'send_community': dict(choices=['both']),
        'state': dict(choices=['present', 'absent'], default='present')
    }

    identifier = ('neighbor', )

    def render(self, config=None):
        commands = list()

        if self.state == 'absent':
            cmd = 'neighbor %s' % self.neighbor
            if not config or cmd in config:
                commands = ['no %s' % cmd]

        elif self.state in ('present', None):
            for attr in self.argument_spec:
                if attr in self.values:
                    meth = getattr(self, '_set_%s' % attr, None)
                    if meth:
                        commands.extend(to_list(meth(config)))

        return commands

    def _set_activate(self, config=None):
        cmd = 'neighbor %s activate' % self.neighbor
        if not config or cmd not in config:
            return cmd

    def _set_description(self, config=None):
        cmd = 'neighbor %s description %s' % (self.neighbor, self.description)
        if not config or cmd not in config:
            return cmd

    def _set_enabled(self, config=None):
        cmd = 'neighbor %s shutdown' % self.neighbor
        if self.enabled is False:
            cmd = 'no %s' % cmd
        if not config or cmd not in config:
            return cmd

    def _set_remote_as(self, config=None):
        cmd = 'neighbor %s remote-as %s' % (self.neighbor, self.remote_as)
        if not config or cmd not in config:
            return cmd

    def _set_send_community(self, config=None):
        cmd = 'neighbor %s send-community %s' % (self.neighbor, self.send_community)
        if not config or cmd not in config:
            return cmd
