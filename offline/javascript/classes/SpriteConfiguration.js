
/**
 * Antoine LANDRIEUX 2024 WTFPL
 * Sprite Configuration class (SpriteConfiguration.js)
 * 
 * <https://github.com/AntoineLandrieux/PxEngine>
 */

export class SpriteConfiguration {

    /**
     * @type {number}
     */
    animation = 0;
    /**
     * @type {number}
     */
    direction = 0;

    /**
     * Sprite Configuration class
     * @param {HTMLImageElement} sprite Sprite image
     * @param {number} animation_count Number of animations
     * @param {number} direction_count Number of direction
     * @param {number} width Width
     * @param {number} height Height
     */
    constructor(

        sprite,
        context,
        animation_count,
        direction_count,
        width,
        height

    ) {

        this.sprite = sprite;
        this.context = context;
        this.animation_count = animation_count;
        this.direction_count = direction_count;
        this.width = width;
        this.height = height;

    }

    /**
     * Show sprite
     * @param {number} x Position
     * @param {number} y Position
     */
    print(x, y) {

        this.context.drawImage(
            this.sprite,
            this.animation * this.width,
            this.direction * this.height,
            this.width,
            this.height,
            x,
            y,
            this.width,
            this.height
        );

    }

    /**
     * Set sprite direction
     * @param {number} direction Direction
     * @returns {number}
     */
    SetDirection(direction) {

        if (!(direction < 0 || direction >= this.direction_count))
            this.direction = direction;
        return this.direction;

    }

    /**
     * Update sprite animation
     * @returns {number}
     */
    UpdateAnimation() {

        this.animation = (this.animation >= (this.animation_count - 1) ? 0 : (this.animation + 1));
        return this.animation;

    }

}
