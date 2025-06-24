
import { getLastAction, clearLastAction } from "../event/EventHandler.js";
import { ctx, HEIGHT, WIDTH } from "../Context.js"
import { Clear, DialogBox, Template, Transition, setScene, setTransition } from "./Scene.js";
import { MainMap } from "./MainMap.js";
import { fight_audio, menu_select, pokeball_sprite, PokemonList, Pokedex } from "../Medias.js";

/**
 * ------------------------------
 * FUNCTION
 * ------------------------------
 */

let pokemon_enemy = null;
let pokemon_player = null;

let is_captured = false;

let dialog = undefined;
let success = undefined;
let attack_dialog = 0;
let capture_dialog = 0;

/**
 * ------------------------------
 * ITEMS
 * ------------------------------
 */

let Potion = 3;
let Pokeball = 3;

/**
 * ------------------------------
 * SOUND
 * ------------------------------
 */

let sound = false;

/* Infinite loop */
fight_audio.addEventListener("ended", function () {

    if (sound) {

        fight_audio.currentTime = 0;
        fight_audio.play();

    }

});

/**
 * Restore all values to default
 */
function Reset() {

    sound = false;
    fight_audio.pause();

    dialog = undefined;
    success = undefined;
    pokemon_enemy = null;
    is_captured = false;
    attack_dialog = 0;
    capture_dialog = 0;

    Win.xp = 0;

}

/**
 * Game Over screen
 */
function GameOver() {

    Clear();

    ctx.font = "50px PokemonClassic";
    ctx.fillStyle = "#ffffff";
    ctx.fillText("GAME OVER", 50, 50);

}

/**
 * Capture pokemon !
 */
function Capture() {

    DialogBox();

    if (capture_dialog == 0) {

        is_captured = true;

        ctx.fillStyle = "#000000";
        ctx.fillText(`You throw a pokeball`, 75, HEIGHT - 175);

    } else {

        if (pokemon_enemy.health < pokemon_enemy.max_health / 2) {

            Pokedex[Pokedex.indexOf(undefined)] = pokemon_enemy.Copy();
            pokemon_enemy.health = 0;

        } else {

            ctx.fillStyle = "#000000";
            ctx.fillText(`${pokemon_enemy.name} has escaped !`, 75, HEIGHT - 175);
            is_captured = false;

        }

    }

    if (getLastAction() == "enter") {

        if (capture_dialog) {

            dialog = 0;

        }

        capture_dialog = !capture_dialog;

    }

}

/**
 * Win screen
 */
function Win() {

    if (!Win.xp) {

        Win.xp = Math.floor(Math.random() * 80) + 10;
        pokemon_player.AddXP(Win.xp);

    }

    DialogBox();

    ctx.font = "20px PokemonClassic";
    ctx.fillStyle = "#000000";
    ctx.fillText(`GG ! You earn ${Win.xp}XP !`, 75, HEIGHT - 175);

    if (getLastAction() == "enter") {
        setTimeout(() => {

            Reset();
            setTransition(MainMap);
            return setScene(Transition);

        }, 1000);
    }

}

/**
 * Pokemon attack
 */
function Attack() {

    DialogBox();
    ctx.font = "20px PokemonClassic";
    ctx.fillStyle = "#000000";

    if (attack_dialog) {

        ctx.fillText(`${pokemon_enemy.name} Attack !`, 75, HEIGHT - 175);
        success = success ?? pokemon_player.Damage(2 + Math.floor(Math.random() * pokemon_enemy.level * 3));

    } else {

        ctx.fillText(`Your ${pokemon_player.name} Attack !`, 75, HEIGHT - 175);
        success = success ?? pokemon_enemy.Damage(2 + Math.floor(Math.random() * pokemon_player.level * 3));

    }

    if (getLastAction() == "enter") {

        menu_select.currentTime = 0;
        menu_select.play();

        success = undefined;
        attack_dialog++;

    }

    if (attack_dialog >= 2) {

        success = undefined;
        attack_dialog = 0;
        dialog = 0;

    }

}

/**
 * Bundle, contains items like potion and pokeball
 */
function Backpack() {

    Backpack.selected = Backpack.selected ?? 0;

    DialogBox();

    switch (getLastAction()) {

        case "escape":

            dialog = 0;

        case "arrowright":

            Backpack.selected = 1;
            break;

        case "arrowleft":

            Backpack.selected = 0;
            break;

        case "enter":

            if (!Backpack.selected) {

                if (Pokeball > 0) {

                    dialog = 4;
                    Pokeball--;

                }

                break;

            }

            if (Backpack.selected) {

                if (Potion > 0) {

                    pokemon_player.Heal(20);
                    Potion--;

                } else {

                    break;

                }

            }

            attack_dialog = 1;
            dialog = 1;

        default:

            break;

    }

    ctx.font = "20px PokemonClassic";

    ctx.fillStyle = !Backpack.selected ? "#EEAA00" : "#000000";
    ctx.fillText(`POKEBALL x${Pokeball}`, 125, HEIGHT - 150);
    ctx.fillStyle = Backpack.selected ? "#EEAA00" : "#000000";
    ctx.fillText(`POTION x${Potion}`, WIDTH - 300, HEIGHT - 150);

    /*
     * TODO: Add items ?
     */

    ctx.fillStyle = "#aeaeae";
    ctx.fillText("NOTHING", 125, HEIGHT - 100);
    ctx.fillText("NOTHING", WIDTH - 300, HEIGHT - 100);

}

/**
 * Switch pokemon
 */
function Switch() {

    Switch.selected = Switch.selected ?? 0;

    DialogBox();

    switch (getLastAction()) {

        case "arrowdown":

            Switch.selected += 2;
            break;

        case "arrowup":

            Switch.selected -= 2;
            break;

        case "arrowright":

            Switch.selected += 1;
            break;

        case "arrowleft":

            Switch.selected -= 1;
            break;

        case "enter":

            if (!Pokedex[Switch.selected])
                break;

            if (Pokedex[Switch.selected].health <= 0)
                break;

            pokemon_player = Pokedex[Switch.selected];

        case "escape":

            dialog = 0;

        default:

            break;

    }

    Switch.selected = Math.max(0, Math.min(3, Switch.selected));

    ctx.font = "20px PokemonClassic";

    ctx.fillStyle = Switch.selected == 0 ? "#EEAA00" : "#000000";
    ctx.fillText(Pokedex[0]?.name ?? "...", 125, HEIGHT - 150);
    ctx.fillStyle = Switch.selected == 1 ? "#EEAA00" : "#000000";
    ctx.fillText(Pokedex[1]?.name ?? "...", WIDTH - 300, HEIGHT - 150);
    ctx.fillStyle = Switch.selected == 2 ? "#EEAA00" : "#000000";
    ctx.fillText(Pokedex[2]?.name ?? "...", 125, HEIGHT - 100);
    ctx.fillStyle = Switch.selected == 3 ? "#EEAA00" : "#000000";
    ctx.fillText(Pokedex[3]?.name ?? "...", WIDTH - 300, HEIGHT - 100);

}

/**
 * Select option (run, fight, backpack, switch)
 */
function Fight() {

    Fight.selected = Fight.selected ?? 0;

    DialogBox();

    switch (getLastAction()) {

        case "arrowdown":

            Fight.selected += 2;
            break;

        case "arrowup":

            Fight.selected -= 2;
            break;

        case "arrowright":

            Fight.selected += 1;
            break;

        case "arrowleft":

            Fight.selected -= 1;
            break;

        case "enter":

            if (Fight.selected == 0) {

                Reset();
                setTransition(MainMap);
                return setScene(Transition);

            }

            dialog = Fight.selected;

        default:

            break;

    }

    Fight.selected = Math.max(0, Math.min(3, Fight.selected));

    ctx.font = "20px PokemonClassic";

    ctx.fillStyle = Fight.selected == 0 ? "#EEAA00" : "#000000";
    ctx.fillText("RUN", 125, HEIGHT - 150);
    ctx.fillStyle = Fight.selected == 1 ? "#EEAA00" : "#000000";
    ctx.fillText("FIGHT", WIDTH - 300, HEIGHT - 150);
    ctx.fillStyle = Fight.selected == 2 ? "#EEAA00" : "#000000";
    ctx.fillText("BACKPACK", 125, HEIGHT - 100);
    ctx.fillStyle = Fight.selected == 3 ? "#EEAA00" : "#000000";
    ctx.fillText("SWITCH", WIDTH - 300, HEIGHT - 100);

}

/**
 * Fight scene
 */
export function FightScene() {

    if (dialog == undefined) {

        fight_audio.currentTime = 0;
        fight_audio.play();
        dialog = 0;

    }

    while (!pokemon_enemy) {

        // Select random pokemon_enemy
        pokemon_enemy = PokemonList[Math.floor(Math.random() * 3)]?.Copy();

    }

    let tmp = 0;

    while (!pokemon_player || pokemon_player.health <= 0) {

        if (Pokedex[tmp]) {

            pokemon_player = Pokedex[tmp];
            tmp++;
            continue;

        }

        clearLastAction();
        return setScene(GameOver);

    }

    Template(false);

    if (!is_captured) {

        ctx.drawImage(pokemon_enemy.sprite, WIDTH / 1.5, HEIGHT / 2 - 100);

    } else {

        ctx.drawImage(pokeball_sprite, WIDTH / 1.5, HEIGHT / 2 - 100);

    }

    pokemon_enemy.Hub("right");

    ctx.save();
    ctx.translate(WIDTH, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(pokemon_player.sprite, WIDTH / 1.5, HEIGHT / 2 - 100);
    ctx.restore();

    pokemon_player.Hub();

    if (pokemon_enemy.health <= 0) {

        return Win();

    }

    switch (dialog) {

        case 0:

            Fight();
            break;

        case 1:

            Attack();
            break;

        case 2:

            Backpack();
            break;

        case 3:

            Switch();
            break;

        case 4:

            Capture();
            break;

        default:

            break;

    }

    clearLastAction();

}
