# try-ovn-in-netns
A simple script tool to deploy a netns environment and play ovn with it.

Needs https://github.com/lizk1989/netns-topo

Currently for now:

  - for setup
    - modify topo-setup.sh and ovn-resource-setup.sh with correct path of
      netns-topo
    - (optional) customize netns-topo.yaml
    - bash topo-setup.sh 
    - bash services-setup.sh 
    - (optional) customize ovn-topo.yaml
    - bash ovn-resource-setup.sh
  - for cleanup
    - bash services-cleanup.sh
    - bash topo-destroy.sh
