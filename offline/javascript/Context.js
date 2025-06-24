/**
 * @type {HTMLCanvasElement}
 */
export const game = document.getElementById("game");
export const ctx = game.getContext("2d");

/**
 * ------------------------------
 * SCREEN RESOLUTION AND SETTINGS
 * ------------------------------
 */

export const WIDTH = 800;
export const HEIGHT = 600;

ctx.textAlign = 'left';
ctx.textBaseline = 'top';
