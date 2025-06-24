import { Camera } from "./Camera.js";
import { Collider } from "./Collide.js";
import { SpriteConfiguration } from "./SpriteConfiguration.js";

/**
 * Antoine LANDRIEUX 2024 WTFPL
 * Player class (Player.js)
 * 
 * <https://github.com/AntoineLandrieux/PxEngine>
 */

export class Player {

    /**
     * @type {object}
     */
    GameRule = {
        Speed: 10
    };

    /**
     * Entity class
     * @param {SpriteConfiguration} spriteConfig Sprite Configuration
     * @param {Collider} collide Collision
     * @param {Camera} camera Camera
     * @param {number} posX Position
     * @param {number} posY Position
     */
    constructor(

        spriteConfig,
        collide = null,
        camera = null,
        posX = 0,
        posY = 0,

    ) {

        this.spriteConfig = spriteConfig;
        this.collide = collide;
        this.camera = camera;
        this.posX = posX;
        this.posY = posY;

    }

    /**
     * Return Position in Game
     * @returns {object}
     */
    GamePosition() {

        return {
            x: this.posX + this.camera.x,
            y: this.posY + this.camera.y
        };

    }

    /**
     * Move entity
     * @param {"up"|"down"|"left"|"right"|"stay"} _Direction Direction
     */
    EntityMove(_Direction) {

        let x = this.posX;
        let y = this.posY;

        this.spriteConfig.SetDirection(this.Direction(_Direction));

        if (this.collide.IsCollide(

            this.posX + this.camera.x,
            this.posY + this.camera.y,
            this.spriteConfig.width,
            this.spriteConfig.height

        )) {

            this.posX = x;
            this.posY = y;

        }

        this.spriteConfig.print(this.posX + this.camera.x, this.posY + this.camera.y);

        if (_Direction.toLowerCase() != "stay")
            this.spriteConfig.UpdateAnimation();
    }

    /**
 * Update entity direction
 * @param {"up"|"down"|"left"|"right"|"stay"} _Direction Direction
 * @returns {number}
 */
    Direction(_Direction) {

        switch (_Direction.toLowerCase()) {

            case "down":
                this.posY += this.GameRule.Speed;
                return 0;

            case "left":
                this.posX -= this.GameRule.Speed;
                return 1;

            case "right":
                this.posX += this.GameRule.Speed;
                return 2;

            case "up":
                this.posY -= this.GameRule.Speed;
                return 3;

            case "stay":
            default:
                break;

        }

        return -1;

    }

    /**
     * Move player and update camera
     * @param {"up"|"down"|"left"|"right"|"stay"} direction Direction
     */
    PlayerMove(direction) {

        let x = this.posX;
        let y = this.posY;

        this.spriteConfig.SetDirection(this.Direction(direction));

        if (this.collide.IsCollide(

            this.posX,
            this.posY,
            this.spriteConfig.width,
            this.spriteConfig.height

        )) {

            this.posX = x;
            this.posY = y;

        }

        this.spriteConfig.print(this.posX, this.posY);

        if (direction.toLowerCase() != "stay")
            this.spriteConfig.UpdateAnimation();

        if (this.posX != x)
            this.camera.x += this.posX > x ? -this.GameRule.Speed : this.GameRule.Speed;

        if (this.posY != y)
            this.camera.y += this.posY > y ? -this.GameRule.Speed : this.GameRule.Speed;

        this.posX = x;
        this.posY = y;

    }

}
