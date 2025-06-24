
import { ctx, HEIGHT, WIDTH } from "../Context.js";
import { clearLastAction } from "../event/EventHandler.js";
import { menu_select } from "../Medias.js";

/**
 * ------------------------------
 * FUNCTION
 * ------------------------------
 */

/* Current scene */
let Scene = null;
/* Transition scene */
let t_scene = null;

/**
 * Clear screen
 * @param {string|CanvasGradient} color 
 */
export function Clear(color = "#000000") {

    ctx.fillStyle = color;
    ctx.fillRect(0, 0, WIDTH, HEIGHT);

}

/**
 * Open new dialog box
 * @param {string} character 
 */
export function DialogBox(character = "...") {

    ctx.fillStyle = "#417579";
    ctx.fillRect(25, HEIGHT - 225, WIDTH - 100, 175);

    ctx.fillStyle = "#f0f8ff";
    ctx.fillRect(WIDTH - 250, HEIGHT - 250, 200, 75);

    ctx.fillStyle = "#dadada";
    ctx.fillRect(50, HEIGHT - 200, WIDTH - 100, 175);

    ctx.fillStyle = "#000000";
    ctx.font = "20px PokemonClassic";
    ctx.fillText(character, WIDTH - 225, HEIGHT - 230);

}

/**
 * Default background for main menu, fight scene, ...
 * @param {boolean} license 
 */
export function Template(license = true) {

    let gradient = ctx.createLinearGradient(0, 100, 0, 500);
    gradient.addColorStop(0, "#498F7B");
    gradient.addColorStop(1, "#417579");

    Clear(gradient);

    ctx.fillStyle = "#0000001f";

    ctx.beginPath();
    ctx.ellipse(WIDTH / 2, 0, WIDTH, 65, 0, 0, 2 * Math.PI);
    ctx.fill();

    ctx.beginPath();
    ctx.ellipse(WIDTH / 2, HEIGHT, WIDTH, 65, 0, 0, 2 * Math.PI);
    ctx.fill();

    ctx.fillStyle = "#ffffff1f";

    ctx.beginPath();
    ctx.ellipse(WIDTH / 2, HEIGHT / 2, 200, 10, 0, 0, 2 * Math.PI);
    ctx.fill();

    if (license) {

        ctx.fillStyle = "#ffffff";
        ctx.font = "20px PokemonXandY";
        ctx.textAlign = "center";
        ctx.fillText("OpenPoke 2025 unofficial Pokemon(tm)", WIDTH / 2, HEIGHT - 40);
        ctx.textAlign = "left";

    }

}

/**
 * Set transition
 * @param {Function} scene 
 */
export function setTransition(scene) {

    t_scene = scene;

}

/**
 * Run Transition
 */
export function Transition() {

    if (!Transition.step) {

        menu_select.currentTime = 0;
        menu_select.play();

        Transition.step = 0;

    }

    Clear("#ffffffa0");
    Transition.step++;

    if (Transition.step == 5) {

        Transition.step = 0;
        setScene(t_scene);

    }

}

/**
 * Set scene
 * @param {Function} fun 
 */
export function setScene(fun) {

    clearLastAction();
    Scene = fun;

}

/**
 * Run current scene
 */
export function runScene() {

    Scene();

}
