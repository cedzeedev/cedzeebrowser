
/**
 * Antoine LANDRIEUX 2024 WTFPL
 * Camera class (Camera.js)
 * 
 * <https://github.com/AntoineLandrieux/PxEngine>
 */

export class Camera {

    /**
     * Camera class
     * @param {number} x Position
     * @param {number} y Position
     * @param {number} screen_width Screen size
     * @param {number} screen_height Screen size
     */
    constructor(

        x = 0,
        y = 0,
        screen_width = 800,
        screen_height = 600

    ) {

        this.x = x;
        this.y = y;
        this.screen_width = screen_width;
        this.screen_height = screen_height;

    }

}
