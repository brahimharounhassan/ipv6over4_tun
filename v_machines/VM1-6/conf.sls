# Configuration eth1
# RAPPEL: eth0 est à vagrant, ne pas y toucher

## Désactivation de network-manager
NetworkManager:
  service:
    - dead
    - enable: False
    
## Suppression de la passerelle par défaut
ip route del default:
  cmd:
    - run

##Configuration de VM1-6
# en statique
eth1:
  network.managed:
    - enabled: True
    - type: eth
    - proto: none
    - enable_ipv4: False
    - ipv6proto: static
    - enable_ipv6: True
    - ipv6_autoconf: no
    - ipv6ipaddr: fc00:1234:1::16
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
    - ipv6ipaddr: fc00:1234:3::16
    - ipv6netmask: 64
 


## Configuration de la route vers LAN4-6 via "VM3"
#routes:
 # network.routes:
  #  - name: eth2
   # - routes:
    #  - name: LAN4-6
     #   ipaddr: fc00:1234:4::/64
      #  gateway: fc00:1234:ffff::2
