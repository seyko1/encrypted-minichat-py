# RSCHAT

Un simple chat sécurisé avec le système de RSA.

## Logiciels
Ce projet à été crée avec : <br>
- Python 3.10 <br>
- TKinter <br>
- Pads <br>

## Setup

### Instalation

Clonez le dépôt sur votre machine :

```
git clone git@code.up8.edu:fgodin/p8-mini-chat.git
```

### Utilisation

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

[@fgodin](https://code.up8.edu/fgodin)<br>
[@dhullot](https://code.up8.edu/dhullot)<br>
[@mhimeur](https://code.up8.edu/mhimeur)<br>
[@Valentin_G](https://code.up8.edu/Valentin_G)<br>
[@nsougoumar](https://code.up8.edu/nsougoumar)<br>
[@aekomono](https://code.up8.edu/aekomono)<br>

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
