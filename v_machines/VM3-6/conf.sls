# Configuration eth1 et eth2
# RAPPEL: eth0 est à vagrant, ne pas y toucher

## Désactivation de network-manager
NetworkManager:
  service:
    - dead
    - enable: False
    
iperf3:
  pkg.installed:
    - refresh: True
    - allow_updates: True   
    
radvd:
  pkg.installed:
    - refresh: True
    - allow_updates: True
    
## Suppression de la passerelle par défaut
ip route del default:
  cmd:
    - run
    
##Configuration de VM1
eth1:
  network.managed:
    - enabled: True
    - type: eth
    - proto: none
    - enable_ipv4: False
    - ipv6proto: static
    - enable_ipv6: True
    - ipv6_autoconf: no
    - ipv6ipaddr: fc00:1234:2::36
    - ipv6netmask: 64
    

eth2:
  network.managed:
    - enabled: True
    - type: eth
    - proto: none
    - enable_ipv4: False
    - ipv6proto: static
    - enable_ipv6: True
    - ipv6_autoconf: no
    - ipv6ipaddr: fc00:1234:4::36
    - ipv6netmask: 64


## Configuration de la route vers LAN3-6 via "VM1"
routes:
  network.routes:
    - name: eth2
    - routes:
      - name: LAN3-6
        ipaddr: fc00:1234:3::/64
        gateway: fc00:1234:4::3
