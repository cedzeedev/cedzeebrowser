import { Pokemon } from "./classes/Pokemon.js";
import { ctx } from "./Context.js";

/**
 * ------------------------------
 * AUDIOS (MUSIC/SOUND EFFECT)
 * ------------------------------
 */

export const map_audio      = new Audio("resources/sound/map/map.wav");
export const fight_audio    = new Audio("resources/sound/map/fight.mp3");
export const menu_cursor    = new Audio("resources/sound/menu/menu_cursor.mp3");
export const menu_select    = new Audio("resources/sound/menu/menu_select.mp3");

/**
 * Load all sound
 */
export function load_sound() {

    map_audio   .load();
    fight_audio .load();
    menu_cursor .load();
    menu_select .load();

}

/**
 * ------------------------------
 * IMAGES (SPRITE/MISC)
 * ------------------------------
 */

export const bulbasaur_sprite   = new Image();
export const squirtle_sprite    = new Image();
export const charmander_sprite  = new Image();

export const pokeball_sprite    = new Image();
export const player_sprite      = new Image();

export const mainmap_tileset    = new Image();

/**
 * Load all images
 */
export function load_image() {

    bulbasaur_sprite    .src = "resources/sprite/bulbasaur.png";
    squirtle_sprite     .src = "resources/sprite/squirtle.png";
    charmander_sprite   .src = "resources/sprite/charmander.png";

    pokeball_sprite     .src = "resources/sprite/pokeball.png";
    player_sprite       .src = "resources/sprite/player.png";

    mainmap_tileset     .src = "resources/tileset/mainmap.png";

}

/**
 * All Pokemons
 * 
 * @type {Pokemon[]}
 */
export const PokemonList = [
    new Pokemon ( charmander_sprite, ctx, "Charmander" ),
    new Pokemon ( squirtle_sprite,   ctx, "Squirtle"   ),
    new Pokemon ( bulbasaur_sprite,  ctx, "Bulbasaur"  )
];

/**
 * Player Pokedex
 * 
 * @type {Pokemon[]}
 */
export let Pokedex = [undefined, undefined, undefined, undefined];
