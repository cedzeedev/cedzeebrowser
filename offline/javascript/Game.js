
import { setScene, runScene } from "./scene/Scene.js";
import { MainMenu } from "./scene/MainMenu.js";
import { load_image, load_sound } from "./Medias.js";

/**
 * 
 * ________                      __________       __
 * \_____  \ ______   ____   ____\______   \____ |  | __ ____
 *  /   |   \\____ \_/ __ \ /    \|     ___/  _ \|  |/ // __ \
 * /    |    \  |_> >  ___/|   |  \    |  (  <_> )    <\  ___/
 * \_______  /   __/ \___  >___|  /____|   \____/|__|_ \\___  >
 *         \/|__|        \/     \/                    \/    \/
 * 
 * OpenPoke 2025 <https://github.com/AntoineLandrieux/OpenPoke> WTFPL
 * 
 */

window.onload = () => {

    // Load sound
    load_sound();
    // Load image
    load_image();

    // Go to main menu
    setScene(MainMenu);
    // Run Scene
    setInterval(runScene, 100);

};
