
# TODO

## ✅ Task List importants

### Les extensions

```txt
extensions
 |
 |---- Mon Extension
 |     |
 |     |---- "autres dossiers/fichiers utile à l'extension"
 |     |---- extension.ico
 |     |---- config.json
 |     |---- main.js 
```

1. Le fichier **config.json**

```json
{
  // Auteur
  "author": "Nom",
  // Descrition
  "description": "Utile et super cool :)",
  // Version MAJEUR.mineur.patch
  "version": "1.0.0",
  // Désactivation totale
  "disabled": false,
  // Désactivation pour un site
  "disabled_for": [
    "http://site.com"
  ]
}
```

2. Le fichier **main.js**

```js
import { Dependences } from "autres_fichiers_utile_a_l_extension.js"

window.addEventListener("load", function (event) => {
  // Le code
});
```

3. Et enfin on l'injecte le **main.js** dans les pages web:

```html
<script src="/../extention.js" type="module"></script>
```

## ✅ Task List optionnels

- [ ] [Sélection de thèmes](https://discord.com/channels/1213892868708503604/1213894739875725383/1391050183449514124) (Repo github avec `theme.cedzeetheme` au format json et `theme.css`)

## En cours : 

- [ ] extension (all)

## Fait : 

- [X] favoris (slohwnix)
- [X] cedzee:// (Slohwnix)
- [X] Refaire le style de `history.html` (slohwnix)
- [X] Afficher la date et l'heure dans l'historique (slohwnix)
- [X] Ouvrir un onglet dans une application (slohwnix)
- [X] nouveaux système de mise à jour (slohwnix)
- [X] système de téléchargements amélioré (slohwnix)
- [X] paramètres
- [X] page de bienvenue pour premier démarrage (slohwnix)
- [X] Lancement rapide du navigateur (Multithreading) fait par slohwnix
- [X] Besoin d'un logo (Logo par Natdev, implémentation par Slohwnix avec l'aide de Gens)
- [X] Finaliser les cedapps
