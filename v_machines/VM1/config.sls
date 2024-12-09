## Désactivation de network-manager
NetworkManager:
  service:
    - dead
    - enable: False 
    
# Installatoin du paquet radvd
radvd-package:
  pkg.installed:
    - name: radvd

# Activation du service radvd
radvd-service:
  service.running:
    - name: radvd
    - enabled: True
    - watch:
      - file: /etc/radvd.conf
 
## Suppression de la passerelle par défaut
ip route del default:
  cmd:
    - run

##Configuration de VM1
eth1:
  network.managed:
    - enabled: True
    - type: eth
    - proto: static
    - ipaddr: 172.16.2.131
    - netmask: 28

eth2:
  network.managed:
    - enabled: True
    - type: eth
    - proto: static
    - enable_ipv4: False
    - ipv6proto: static
    - enable_ipv6: True
    - ipv6_autoconf: no
    - ipv6ipaddr: fc00:1234:3::1
    - ipv6netmask: 64          

## Configuration de la route vers LAN2 via VM2
routes:
  network.routes:
    - name: eth1
    - routes:
      - name: LAN2
        ipaddr: 172.16.2.160/28
        gateway: 172.16.2.132

## Enable ipv6 forwarding
net.ipv6.conf.all.disable_ipv6:
  sysctl:
    - present
    - value: 0
    
## Enable ipv6 forwarding
net.ipv6.conf.all.forwarding:
  sysctl:
    - present
    - value: 1
    
## Enable ipv4 forwarding
net.ipv4.ip_forward:
  sysctl:
    - present
    - value: 1
    
net.ipv6.conf.eth2.accept_ra:
  sysctl:
    - present
    - value: 1
