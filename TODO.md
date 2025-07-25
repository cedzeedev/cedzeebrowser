
# TODO

## ✅/❌ Important Task List

- [ ] Navigation privée
- [ ] Les tabs améliorées (CSS) [more info](https://discord.com/channels/1213892868708503604/1213894739875725383/1397234722685325373)
- [ ] Le ctrl+f pour rechercher dans une page web (Vérifier si c'est possible) [more info](https://discord.com/channels/1213892868708503604/1213894739875725383/1397253483043753985)
- [ ] Quand on n'écrit pas un lien dans la barre d'URL ça nous lance une recherche avec le moteur sélectionné
- [ ] Des recommandations dans le moteur de recherche avec l'historique
- [ ] Opti du code (+ ajouter des commentaires et de la doc)
- [ ] [Les extensions](#extensions)

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

window.addEventListener("DOMContentLoaded", function (event) => {

  // code here

});
```

#### And finally we inject the **main.js** into web pages

```html
<script src="/../extension.js" type="module"></script>
```

## ✅/❌ Optional Task List

- [ ] Option "➕ Nouvel onglet (ctrl+t)" dans la liste des tabs
- [ ] Option "❌ Fermer les autres onglets" quand on fait un click droit sur un onglet
- [ ] Option "🔇 Désactiver le son de l'onglet" quand on fait un click droit sur un onglet
- [ ] [Themes](https://discord.com/channels/1213892868708503604/1213894739875725383/1391050183449514124) (Repo github avec `theme.cedzeetheme` au format json et `theme.css`/`browser.css`)

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
