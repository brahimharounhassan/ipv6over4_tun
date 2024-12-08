#!/bin/bash

# Vérifier si un fichier a été passé en argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <fichier.txt>"
    exit 1
fi

# Fichier d'entrée
file="$1"

# Lire le fichier ligne par ligne
while IFS='=' read -r key value; do
    # Ignorer les lignes commentées ou vides
    if [[ $key =~ ^#.* ]] || [[ -z $key ]]; then
        continue
    fi

    # Supprimer les espaces et les guillemets autour des valeurs
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs | sed 's/^"//;s/"$//')

    # Exporter les variables dynamiquement
    declare "$key"="$value"
done < "$file"

sudo python3 tuninit.py $tun $tunaddr $inip $inport $outip $outport $ipv4_gateway $ipv6_gateway $ipv6_dst_lan