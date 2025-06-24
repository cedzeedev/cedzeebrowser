import { Camera } from "./Camera.js";
import { Collider } from "./Collide.js";

/**
 * Antoine LANDRIEUX 2024 WTFPL
 * WorldMap class (WorldMap.js)
 * 
 * <https://github.com/AntoineLandrieux/PxEngine>
 */

export class WorldMap {

    /**
     * WorldMap class
     * @param {CanvasRenderingContext2D} context Context
     * @param {object} map Map
     * @param {Camera} camera Camera
     * @param {Collider} collide Collision
     */
    constructor(

        context,
        map,
        camera,
        collide

    ) {

        this.context = context;
        this.map = map;
        this.camera = camera;
        this.collide = collide;
        this.tileset = map.Tileset;

    }

    /**
     * Show the map
     */
    print() {

        this.collide.clear();

        for (let y = 0; y < this.map.World.length; y++) {
            for (let x = 0; x < this.map.World[y].length; x++) {

                if (this.map.Collide.includes(this.map.World[y][x])) {
                    this.collide.Register(
                        x * this.map.TilesizeW + this.camera.x,
                        y * this.map.TilesizeH + this.camera.y,
                        this.map.TilesizeW,
                        this.map.TilesizeH
                    );
                }

                this.context.drawImage(

                    this.tileset,
                    (this.map.World[y][x] - 1) * this.map.TilesizeW,
                    0,
                    this.map.TilesizeW,
                    this.map.TilesizeH,
                    x * this.map.TilesizeW + this.camera.x,
                    y * this.map.TilesizeH + this.camera.y,
                    this.map.TilesizeW,
                    this.map.TilesizeH

                );

            }
        }

    }

}
