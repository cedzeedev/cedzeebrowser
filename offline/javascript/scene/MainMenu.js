
import { getLastAction, clearLastAction } from "../event/EventHandler.js";
import { ctx, WIDTH, HEIGHT } from "../Context.js";
import { Template, Transition, setTransition, setScene } from "./Scene.js";
import { menu_cursor, menu_select } from "../Medias.js";
import { Intro } from "./Intro.js";

/**
 * Show all commands
 */
function Commands() {

    Template();

    ctx.font = "20px PokemonClassic";
    ctx.fillStyle = "#ffff00";
    ctx.fillText("Commands (Press Escape to quit)", 50, 150);

    ctx.fillStyle = "#ffffff";
    ctx.fillText("PAUSE:", 50, 200);
    ctx.fillText("Escape", WIDTH / 2, 200);
    ctx.fillText("CONFIRM:", 50, 250);
    ctx.fillText("Enter", WIDTH / 2, 250);
    ctx.fillText("RIGHT:", 50, 300);
    ctx.fillText("Arrow Right", WIDTH / 2, 300);
    ctx.fillText("LEFT:", 50, 350);
    ctx.fillText("Arrow Left", WIDTH / 2, 350);
    ctx.fillText("UP:", 50, 400);
    ctx.fillText("Arrow Up", WIDTH / 2, 400);
    ctx.fillText("DOWN:", 50, 450);
    ctx.fillText("Arrow Down", WIDTH / 2, 450);

    if (getLastAction() == "escape") {

        setScene(MainMenu);

    }

}

/**
 * Show infos
 */
function Infos() {

    Template();

    ctx.font = "20px PokemonClassic";
    ctx.fillStyle = "#ffff00";
    ctx.fillText("Infos (Press Escape to quit)", 50, 150);

    ctx.fillStyle = "#ffffff";
    ctx.fillText("===== Antoine LANDRIEUX", 50, 200);
    ctx.fillText(" - https://github.com/AntoineLandrieux/", 50, 250);
    ctx.fillText("===== The Pokemon Company", 50, 300);
    ctx.fillText(" - https://www.pokemon.com/", 50, 350);
    ctx.fillText(" - (unofficial Pokemon game)", 50, 400);


    if (getLastAction() == "escape") {

        setScene(MainMenu);

    }

}

/**
 * Main menu
 */
export function MainMenu() {

    MainMenu.selected = MainMenu.selected ?? 0;

    const options = ["Play", "Commands", "Infos"];

    switch (getLastAction()) {

        case "arrowleft":
        case "arrowup":

            menu_cursor.currentTime = 0;
            menu_cursor.play();

            if (MainMenu.selected > 0)
                MainMenu.selected -= 1;
            else
                MainMenu.selected = options.length - 1;
            break;

        case "arrowright":
        case "arrowdown":

            menu_cursor.currentTime = 0;
            menu_cursor.play();

            if (MainMenu.selected < options.length - 1)
                MainMenu.selected += 1;
            else
                MainMenu.selected = 0;
            break;

        case "enter":

            menu_select.currentTime = 0;
            menu_select.play();

            switch (MainMenu.selected) {
                case 0:
                    setTransition(Intro);
                    return setScene(Transition);
                case 1:
                    return setScene(Commands);
                case 2:
                    return setScene(Infos);
                default:
                    break;
            }

        default:
            break;
    }

    Template();

    ctx.font = "100px PokemonSolid";
    ctx.fillStyle = "#ffffff";
    ctx.textAlign = "center";
    ctx.fillText("OpenPoke", WIDTH / 2, HEIGHT / 2 - 125);
    ctx.textAlign = "left";

    ctx.font = "20px PokemonClassic";

    for (let i in options) {

        ctx.fillStyle = MainMenu.selected == i ? "#ffff00" : "#ffffff";
        ctx.fillText(MainMenu.selected == i ? ">>>" : "[", 50, 350 + i * 50);
        ctx.fillText(options[i], 105, 350 + i * 50);

    }

    clearLastAction();

}

