#!/usr/bin/python2.7
#
# run as root

import netaddr
import os
import yaml


def get_topo(filename):
    ret = {}
    with open(filename) as f:
        ret.update(yaml.safe_load(f) or {})
    return ret


def get_dev_name(node, switch):
    ovs_dev_name = '%s-%so' % (switch, node)
    ns_dev_name = '%s-%sn' % (switch, node)
    if len(ovs_dev_name) > 15:
        raise ValueError(
            "LSP %(name)s is too long after trans. len(%(ret)s)>15)" % {
                'name': name, 'ret': dev_name})
    return ovs_dev_name, ns_dev_name


def add_netns(ns_name):
    return 'ip netns add %s' % ns_name


def del_netns(ns_name):
    return 'ip netns del %s' % ns_name


def setup_lo(ns_name):
    return 'ip netns exec %s ip l set lo up' % ns_name


def setup_interface(node, switch, mac_cidrs, chassis, chassis_sock):
    ovs_dev, ns_dev = get_dev_name(node, switch)
    mac, cidrs = mac_cidrs.split(' ', 1)
    ret = [
        'ovn-nbctl lsp-add %(switch)s %(switch)s-%(node)s',
        'ovn-nbctl lsp-set-addresses %(switch)s-%(node)s "%(mac_cidrs)s"',
        'ip netns add %(node)s',
        'ip l add %(ovs_dev)s type veth peer name %(ns_dev)s netns %(node)s',
        'ip l set %(ovs_dev)s netns %(chassis)s',
        'ip netns exec %(chassis)s ip l set %(ovs_dev)s up',
        ('ip netns exec %(chassis)s ovs-vsctl '
         '--db=unix:%(chassis_sock)s add-port br-int %(ovs_dev)s'),
        'ip netns exec %(node)s ip l set %(ns_dev)s up',
        'ip netns exec %(node)s ip l set %(ns_dev)s address %(mac)s',
        ('ovs-vsctl --db=unix:%(chassis_sock)s set interface %(ovs_dev)s '
         'external_ids:iface-id=%(switch)s-%(node)s')]
    ret.extend([
        'ip netns exec %(node)s ip a add dev %(ns_dev)s %(cidr)s' % {
            'node': node, 'ns_dev': ns_dev, 'cidr': cidr}
        for cidr in cidrs.split()])
    return '\n'.join(ret) % {
        'node': node, 'ovs_dev': ovs_dev, 'ns_dev': ns_dev, 'switch': switch,
        'chassis': chassis, 'chassis_sock': chassis_sock, 'mac': mac,
        'mac_cidrs': mac_cidrs}


def destroy_interface(ns_name, ns_type, switch):
    dev_name = get_dev_name(ns_name, switch)
    return 'ip l del %s' % dev_name


def add_default_route(ns_name, nexthop):
    return 'ip netns exec %(ns_name)s ip r add default via %(nh)s' % {
        'ns_name': ns_name, 'nh': nexthop}


def add_extra_route(ns_name, dest, nexthop):
    return 'ip netns exec %(ns_name)s ip r add %(dest)s via %(nh)s' % {
        'ns_name': ns_name, 'dest': dest, 'nh': nexthop}


def setup_node(name, info):
    chassis = info['chassis']
    chassis_sock = info['chassis_sock']
    ret = [
        setup_interface(name, switch, mac_cidrs, chassis, chassis_sock)
        for (switch, mac_cidrs) in info['interfaces'].iteritems()]
    #ret.append(add_default_route(name, info['default_route']))
    ret.append(setup_lo(name))
    ret.extend([
        add_extra_route(name, dest, nexthop)
        for (dest, nexthop) in info.get('extra_routes', {}).iteritems()])
    return '\n'.join(ret), False


def destroy_node(name, info):
    ret = [
        destroy_interface(name, 'node', sw) for sw in info['interfaces']]
    ret.append(del_netns(name))
    return '\n'.join(ret), True


def setup_switch(name, info):
    return 'ovn-nbctl ls-add %s' % name, True


def destroy_switch(name, info):
    return 'ovs-nbctl ls-del %s' % name, True


def setup_router(name, info):
    return '', True


def destroy_router(name, info):
    return '', True


def pre_check(topo_d, name, info):
    for switch, mac_cidrs in info.get('interfaces', {}).iteritems():
        switch_cidrs = topo_d.get(switch, {}).get('cidr')
        if not switch_cidrs:
            raise ValueError('switch %s not found or has no cidrs' % switch)
        switch_cidrs = switch_cidrs.split()
        try:
            switch_nets = [netaddr.IPNetwork(cidr) for cidr in switch_cidrs]
        except Exception:
            raise ValueError('switch %s has an invalid cidr' % switch)
        mac, cidrs = mac_cidrs.split(' ', 1)
        if not netaddr.valid_mac(mac):
            raise ValueError(
                "%(name)s interface has an invalid mac %(mac)s" % {
                    'name': name, 'mac': mac})
        cidrs = cidrs.split()
        try:
            intf_nets = [netaddr.IPNetwork(cidr) for cidr in cidrs]
        except Exception:
            raise ValueError(
                '%(name)s interface on %(switch)s has an invalid cidr' % {
                    'name': name, 'switch': switch})
        if set(intf_nets) - set(switch_nets):
            raise ValueError(
                "Not all %(name)s interface cidr in its %(switch)s" % {
                    'name': name, 'switch': switch})
        chassis = info.get('chassis')
        if not (chassis and os.path.exists('/var/run/netns/%s' % chassis)):
            raise ValueError(
                ("%s interface doesn't have an valid 'chassis' to indicate "
                 "which chassis it resides on") % name)
        chassis_sock = info.get('chassis_sock')
        if not (chassis_sock and os.path.exists(chassis_sock)):
            raise ValueError(
                "%s interface doesn't have an valid 'chassis_sock'" % name)


def setup_or_destroy(topo_d, method):
    cmds = []
    setup_methods = {
        'node': setup_node,
        'switch': setup_switch,
        'router': setup_router}
    destroy_methods = {
        'node': destroy_node,
        'switch': destroy_switch,
        'router': destroy_router}
    methods = {'setup': setup_methods, 'destroy': destroy_methods}

    try:
        for name, info in topo_d.iteritems():
            _type = info['type']
            if _type not in setup_methods:
                raise ValueError(
                    "Invalid type: %s. Not in (node, switch, router)." % _type)

            if method == 'setup':
                pre_check(topo_d, name, info)
            cmd, top = methods[method][_type](name, info)
            if top:
                cmds.insert(0, cmd)
            else:
                cmds.append(cmd)
    except ValueError as e:
        print e.message
        return
    else:
        cmd_file = './%s_netns_topo_cmds' % method
        with open(cmd_file, 'w+') as f:
            f.write('\n'.join(cmds))
        os.system('bash %s' % cmd_file)
        os.remove(cmd_file)


if __name__ == '__main__':
    def _help():
        print 'python run.py {setup|destroy} topo.yaml'
        os.sys.exit(0)

    if len(os.sys.argv) >= 3:
        method, topo_yaml = os.sys.argv[1:3]
        if method not in ('setup', 'destroy'):
            _help()
        if not os.path.exists(topo_yaml):
            print 'Need a topology yaml file'
            os.sys.exit(1)
        topo_d = get_topo(topo_yaml)
        if not topo_d:
            print "No invalid yaml topo found."
            os.sys.exit(1)
        setup_or_destroy(topo_d, method)
    else:
        _help()
