## Désactivation de network-manager
NetworkManager:
  service:
    - dead
    - enable: False
    
# Installation du paquet netcat(6)
netcat-openbsd:
  pkg.installed:
    - refresh: True
    - allow_updates: True 

# Installation de l’utilitaire iperf3
iperf3:
  pkg.installed:
    - refresh: True
    - allow_updates: True   

# Installation du paquet radvd    
radvd:
  pkg.installed:
    - refresh: True
    - allow_updates: True
    
## Suppression de la passerelle par défaut
ip route del default:
  cmd:
    - run

##Configuration des interface eth1 et eth2 de VM1-6, en statique
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
 
## Configuration de la route vers LAN4-6 via "VM1"
routes:
  network.routes:
    - name: eth2
    - routes:
      - name: LAN3-6
        ipaddr: fc00:1234:ffff::/64
        gateway: fc00:1234:3::1
      - name: LAN4-6
        ipaddr: fc00:1234:4::/64
        gateway: fc00:1234:3::1
        
