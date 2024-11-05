# Messagerie instantannée sécurisée

Implémentation d'un mini-chat minimaliste qui permet à un ensemble de personnes d'échanger des messages de manière sécurisée.

## Logiciels
Ce projet à été crée avec : <br>
- Python 3.10 <br>
- TKinter <br>

## Installation

Clonez le dépôt sur votre machine :

```
git clone git@code.up8.edu:fgodin/p8-mini-chat.git
```

## Utilisation

Pour démarrer le serveur, ouvrez un terminal et exécutez :

```
python3 serveur.py
```


Pour démarrer le client, ouvrez un ou plusieurs terminaux et exécutez :

```
python3 client.py
```

## Exemples

<img src="documentation/images/server-example.png" alt="" width="384" />

*Lancement du serveur depuis un terminal*

---

<img src="documentation/images/clients-example.png" alt="" width="576" />

*Aperçu de deux interfaces de discussion simultanée entre deux utilisateurs Alice et Bob.*

## Contributeurs

[Anyce Ekomono](https://code.up8.edu/aekomono)  
[Dounia Hullot](https://code.up8.edu/dhullot)  
[François Godin](https://code.up8.edu/fgodin)  
[Maëva Himeur](https://code.up8.edu/mhimeur)  
[Neha Sougoumar](https://code.up8.edu/nsougoumar)  
[Valentin Guillon](https://code.up8.edu/Valentin_G)

## Ressources

### Liens pads

[Détail des consignes du projet](https://pads.up8.edu/rj6S3VS3R5W_QRial1zb7g#)

### Schémas
 
<img src="documentation/images/encryption-between-two-clients.png" alt="" width="576" />

*Chiffrement entre deux clients*  

**DH** : Diffie Helmann  
**KsDH** : Clé secrète DH  
**Kss** : Clé secrète signature  
**Ksp** : Clé publique signature  
**A1 / B1** : Transport publique pour DH  
**H(...)** : Fonction de hachage pour RSA  
