# Complexité
![Python 3.8.0](https://img.shields.io/badge/Python-3.8.0-yellow?style=plastic)
<!-- ```
cd existing_repo
git remote add origin https://etulab.univ-amu.fr/master-1/complexite.git
git branch -M main
git push -uf origin main
``` -->

## Nom
Projet de Réseau.

## Description
Le but de ce projet est de permettre des communications entre îlots IPv6 en utilisants des tunnels simples au-dessus de IPv4.
[alt text](https://etulab.univ-amu.fr/b24024546/projet_reseau/-/blob/main/images/reseau6-tun.png?raw=true)

## Structure du projet

Ceci montre brièvement comment ce mini-projet est organisé :

- [x] `images/`: contenant l'image d'illustration:
    - `reseau6-tun.png` 
- [x] `scripts/`: contient tous les scripts python.
    - `conf1.sh` : contient des commandes de configuration permettant de lancer le tunnel étant dans la machine virtuelle 1.
    - `conf3.sh` : contient des commandes de configuration permettant de lancer le tunnel à partir de la machine virtuelle 3.
    - `tunalloc.py` : fichier dans lequel se trouve la bibliothèque `Iftun` qui a pour but de créer l’interface virtuelle.
    - `extremity.py` : fichier contenant la bibliothèque `Extremite` dans laquelle se trouvent les fonctions `ext_out` : qui permet de créer une extrémité qui retransmet le trafic provenant de la socket TCP dans le tun0 local. et la fonction `ext_in`  qui ouvre une connexion TCP avec l’autre extrémité du tunnel, puis lit le trafic provenant de tun0 et le retransmet dans la socket.
    - `tuninit1.py` : Script permettant d'initialiser la bibliothèque `Iftun` afin de créer l'interface virtuelle et lancer le server permettant la communication à partir de la machine VM1.
    - `tuninit3.py` : Script permettant d'initialiser la bibliothèque `Iftun` afin de créer l'interface virtuelle et lancer le server permettant la communication à partir de la machine VM3.
		



## Usage
Cloner le projet via un terminal dans un dossier donné:
```
clone https://etulab.univ-amu.fr/b24024546/projet_reseau.git
cd projet_reseau/scripts/

# Exécution à partir de VM1:
sudo chmod +x conf1.sh
./conf1.sh

# Exécution à partir de VM3:
sudo chmod +x conf3.sh
./conf3.sh
```

## Auteurs 
- [Brahim Haroun Hassan]
- [DIALLO Ismaila]
- [GUERRIER Vanessa]


## License
Academic Free License ("AFL") v. 3.0

## Statut du projet
En cours.

# Références

- [Projet Réseaux](https://pageperso.lis-lab.fr/emmanuel.godard/enseignement/tps-reseaux/projet/)