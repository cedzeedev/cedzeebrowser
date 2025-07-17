
# TODO

## ✅/❌ Important Task List

### Extensions

```txt
extensions
 |---- My Extension
 |     |---- "other folders/files"
 |     |---- config.json
 |     |---- extension.ico
 |     |---- main.js 
```

#### The **config.json** file

```json
{
  // Author
  "author": "Name",
  // Description
  "description": "Useful and super cool :)",
  // Version MAJOR.minor.patch
  "version": "1.0.0",
  // Disabled
  "disabled": false,
  // Enabled for website
  "enabled_for": [],
  // Disabled for website
  "disabled_for": [
    "http://site.com"
  ]
}
```

#### The **main.js** file

```js
import { Dependencies } from "extern_file.js"

window.addEventListener("load", function (event) => {

  // code here

});
```

#### And finally we inject the **main.js** into web pages

```html
<script src="/../extension.js" type="module"></script>
```

## ✅/❌ Optional Task List

- [ ] [Themes](https://discord.com/channels/1213892868708503604/1213894739875725383/1391050183449514124) (Repo github avec `theme.cedzeetheme` au format json et `theme.css`)

## 🧑‍💻 In progress

- [ ] extension (all)

## ✅ Done

- [X] Favoris (slohwnix)
- [X] cedzee:// (Slohwnix)
- [X] Refaire le style de `history.html` (slohwnix)
- [X] Afficher la date et l'heure dans l'historique (slohwnix)
- [X] Ouvrir un onglet dans une application (slohwnix)
- [X] Nouveaux système de mise à jour (slohwnix)
- [X] Système de téléchargements amélioré (slohwnix)
- [X] Paramètres
- [X] Page de bienvenue pour premier démarrage (slohwnix)
- [X] Lancement rapide du navigateur (Multithreading) fait par slohwnix
- [X] Besoin d'un logo (Logo par Natdev, implémentation par Slohwnix avec l'aide de Gens)
- [X] Finaliser les cedapps
