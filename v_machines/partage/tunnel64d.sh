#!/bin/bash

# Vérifier si un argument a été passé pour le fichier de configuration
if [ -z "$1" ]; then
    echo "Erreur : aucun fichier de configuration spécifié."
    echo "Usage: $0 <fichier_config>"
    exit 1
fi

# Nom du fichier de configuration passé en argument
config_file="$1"

# Vérifier si le fichier existe
if [ ! -f "$config_file" ]; then
    echo "Erreur : Le fichier '$config_file' n'existe pas."
    exit 1
fi

# Lire les valeurs à partir du fichier de configuration
while IFS= read -r line; do
    # Vérifier si la ligne contient une configuration et l'ignorer si c'est un commentaire
    if [[ "$line" =~ ^[a-zA-Z] ]]; then
        # Utiliser grep et awk pour extraire les valeurs
        if [[ "$line" =~ ^tun= ]]; then
            tun=$(echo "$line" | awk -F= '{print $2}')
        elif [[ "$line" =~ ^inip= ]]; then
            inip=$(echo "$line" | awk -F= '{print $2}')
        elif [[ "$line" =~ ^inport= ]]; then
            inport=$(echo "$line" | awk -F= '{print $2}')
        elif [[ "$line" =~ ^options= ]]; then
            options=$(echo "$line" | awk -F= '{print $2}')
        elif [[ "$line" =~ ^outip= ]]; then
            outip=$(echo "$line" | awk -F= '{print $2}')
        elif [[ "$line" =~ ^outport= ]]; then
            outport=$(echo "$line" | awk -F= '{print $2}')
        fi
    fi
done < "$config_file"


sudo python3 tuninit.py $tun $options $inip $inport $outip $outport