# Configuration eth1 et eth2
# RAPPEL: eth0 est à vagrant, ne pas y toucher

## Désactivation de network-manager
NetworkManager:
  service:
    - dead
    - enable: False
    
install_tcpdump:
  pkg.installed:
    - name: tcpdump
    - refresh: True
    
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
    - ipaddr: 172.16.2.163
    - netmask: 28

eth2:
  network.managed:
    - enabled: True
    - type: eth
    - proto: none
    - enable_ipv4: false
    - ipv6proto: static
    - enable_ipv6: true
    - ipv6_autoconf: no
    - ipv6ipaddr: fc00:1234:4::3
    - ipv6netmask: 64

## Configuration de la route vers LAN1 via VM2
routes:
  network.routes:
    - name: eth1
    - routes:
      - name: LAN1
        ipaddr: 172.16.2.128/28
        gateway: 172.16.2.162

      
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
