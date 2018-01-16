ovn-nbctl ls-add ls1
ovn-nbctl lsp-add ls1 p1
ovn-nbctl lsp-add ls1 p2
ovn-nbctl lsp-set-addresses p1 "fa:16:3e:00:00:01 10.1.0.11"
ovn-nbctl lsp-set-addresses p2 "fa:16:3e:00:00:02 10.1.0.12"

for p in n1p1 n1p2; do
    ip netns add $p
    ip l add ${p}o type veth peer name ${p}n netns $p
    node="node1"
    if [[ $p == "n1p2" ]]; then
        node="node2"
    fi
    ip l set ${p}o netns $node
    ip netns exec $node ip l set ${p}o up
    ip netns exec $node ovs-vsctl --db=unix:/usr/local/var/run/openvswitch/${node}/db.sock add-port br-int ${p}o

    ip netns exec $p ip l set ${p}n up
    ip netns exec $p ip l set ${p}n address fa:16:3e:00:00:0${p:3:1}
    ip netns exec $p ip a add dev ${p}n 10.1.0.1${p:3:1}/24

    ip netns exec $node ovs-vsctl --db=unix:/usr/local/var/run/openvswitch/${node}/db.sock set interface ${p}o external_ids:iface-id=${p:2:2}
done
