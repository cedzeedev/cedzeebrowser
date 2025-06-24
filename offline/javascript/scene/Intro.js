
import { getLastAction, clearLastAction } from "../event/EventHandler.js";
import { ctx, HEIGHT } from "../Context.js";
import { Clear, DialogBox, setScene, setTransition, Transition } from "./Scene.js";
import { MainMap } from "./MainMap.js";
import { bulbasaur_sprite, squirtle_sprite, fight_audio, menu_cursor, PokemonList, charmander_sprite, Pokedex } from "../Medias.js";

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
 * ------------------------------
 * DIALOGS
 * ------------------------------
 */

const dialogs = [

    // 0
    "Huh??",
    // 1
    "So.. you're new?",
    // 2
    "Good...",
    // 3
    "Let me introduce myself.",
    // 4
    "I am Professor Layton.\nAnd this island is Ophenia.",
    // 5
    "You'll have to defend yourself against\nall the Pokemon on this island.",
    // 6
    "But first..",
    // 7
    "You must choose a Pokemon.",
    // 8
    "Pick one.",
    // 9
    "Excellent choice!",
    // 10
    "And now..",
    // 11
    "Good luck"

];

/**
 * Select Starter
 */
function SelectPokemon() {

    SelectPokemon.selected = SelectPokemon.selected ?? 0;

    if (Intro.dialog == 8) {

        ctx.font = "20px PokemonClassic";

        ctx.fillStyle = SelectPokemon.selected == 0 ? "#ffff00" : "#ffffff";
        ctx.fillText("Charmander", 100, HEIGHT / 2 - 140);
        ctx.fillStyle = SelectPokemon.selected == 1 ? "#ffff00" : "#ffffff";
        ctx.fillText("Squirtle", 350, HEIGHT / 2 - 150);
        ctx.fillStyle = SelectPokemon.selected == 2 ? "#ffff00" : "#ffffff";
        ctx.fillText("Bulbasaur", 550, HEIGHT / 2 - 140);

        switch (getLastAction()) {

            case "enter":

                Pokedex[0] = PokemonList[SelectPokemon.selected]?.Copy();
                return;

            case "arrowleft":

                clearLastAction();
                menu_cursor.currentTime = 0
                menu_cursor.play();

                if (SelectPokemon.selected > 0) {

                    SelectPokemon.selected -= 1;

                }

                break;

            case "arrowright":

                clearLastAction();
                menu_cursor.currentTime = 0
                menu_cursor.play();

                if (SelectPokemon.selected < 2) {

                    SelectPokemon.selected += 1;

                }

                break;

            default:

                break;

        }

    }

    if ((Intro.dialog > 8 && SelectPokemon.selected == 0) || Intro.dialog == 8) {

        ctx.drawImage(charmander_sprite, 150, HEIGHT / 2 - 90);

    }

    if ((Intro.dialog > 8 && SelectPokemon.selected == 1) || Intro.dialog == 8) {

        ctx.drawImage(squirtle_sprite, 350, HEIGHT / 2 - 100);

    }

    if ((Intro.dialog > 8 && SelectPokemon.selected == 2) || Intro.dialog == 8) {

        ctx.drawImage(bulbasaur_sprite, 550, HEIGHT / 2 - 90);

    }

}

/**
 * Introduction
 */
export function Intro() {

    if (Intro.dialog == undefined) {

        fight_audio.currentTime = 0;
        fight_audio.play();

        Intro.dialog = 0;

    }

    sound = true;

    Clear();

    let say = dialogs[Intro.dialog].split("\n");

    DialogBox(Intro.dialog < 4 ? "???" : "Layton");

    ctx.fillText(say[0], 75, HEIGHT - 175)
    ctx.fillText(say[1] ?? "", 75, HEIGHT - 125);

    if (Intro.dialog >= 7) {

        SelectPokemon();

    }

    if (getLastAction() == "escape") {

        menu_cursor.currentTime = 0;
        menu_cursor.play();

        Intro.dialog -= !Intro.dialog ? 0 : 1;
        clearLastAction();

    }

    if (getLastAction() == "enter") {

        menu_cursor.currentTime = 0;
        menu_cursor.play();

        Intro.dialog += 1;
        clearLastAction();

    }

    if (Intro.dialog == dialogs.length - 1) {

        fight_audio.volume = 0.25;

    }

    if (Intro.dialog == dialogs.length) {

        sound = false;
        fight_audio.pause();
        fight_audio.volume = 1;
        Intro.dialog = undefined;
        setTransition(MainMap);
        return setScene(Transition);

    }

}
