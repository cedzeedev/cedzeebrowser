
import { getLastAction, clearLastAction } from "./../event/EventHandler.js";
import { ctx, HEIGHT, WIDTH } from "./../Context.js"
import { Clear, setScene, setTransition, Transition } from "./Scene.js";
import { menu_select, map_audio, player_sprite } from "../Medias.js";

import { Camera } from "../classes/Camera.js";
import { Player } from "../classes/Player.js";
import { SpriteConfiguration } from "../classes/SpriteConfiguration.js";
import { WorldMap } from "../classes/WorldMap.js";
import { Collider } from "../classes/Collide.js";
import { OverWorld } from "./../map/overworld.js";
import { FightScene } from "./FightScene.js";

/**
 * ------------------------------
 * SOUND
 * ------------------------------
 */

let sound = false;

/* Infinite loop */
map_audio.addEventListener("ended", function () {

    if (sound) {

        map_audio.currentTime = 0;
        map_audio.play();

    }

});

/**
 * ------------------------------
 * PLAYER
 * ------------------------------
 */

const player_camera = new Camera(0, 0, WIDTH, HEIGHT)
const collider = new Collider();

const player = new Player(
    new SpriteConfiguration(
        player_sprite,
        ctx,
        4,
        4,
        48,
        68
    ),
    collider,
    player_camera,
    WIDTH / 2,
    HEIGHT / 2
);

/**
 * ------------------------------
 * WORLD
 * ------------------------------
 */

const world = new WorldMap(ctx, OverWorld, player_camera, collider);

/**
 * Pause Menu
 */
function Pause() {

    if (!Pause.draw) {

        sound = false;
        map_audio.pause();

        Clear("#000000a0");

        ctx.fillStyle = "#ffffff";
        ctx.font = "20px PokemonClassic";
        ctx.fillText("PAUSE", 100, 100);

        ctx.fillStyle = "#ffff00";
        ctx.fillText("Press Enter to continue...", 100, 150);

        Pause.draw = true;

    }

    // Quit pause menu
    if (getLastAction() == "enter") {

        Pause.draw = false;
        return setScene(MainMap);

    }

}

/**
 * Main map
 */
export function MainMap() {

    // Play sound (map_audio)
    if (!sound) {

        sound = true;
        map_audio.play();

    }

    // Show world
    Clear("#67E6D2");
    world.print();

    // Player logic
    switch (getLastAction()) {

        // Pause
        case "escape":

            menu_select.currentTime = 0;
            menu_select.play();

            return setScene(Pause);

        // Move left
        case "arrowleft":

            player.PlayerMove("left");
            break;

        // Move up
        case "arrowup":

            player.PlayerMove("up");
            break;

        // Move down
        case "arrowdown":

            player.PlayerMove("down");
            break;

        // Move right
        case "arrowright":

            player.PlayerMove("right");
            break;

        // Stay at current position
        default:

            player.PlayerMove("stay");
            break;

    }

    // Random new fight
    if (Math.floor(Math.random() * 200) == 1) {

        sound = false;

        map_audio.pause();
        map_audio.currentTime = 0;

        setTransition(FightScene);
        return setScene(Transition);

    }

    // Clear last action
    clearLastAction();

}
