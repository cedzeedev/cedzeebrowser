
/**
 * Antoine LANDRIEUX 2024 WTFPL
 * Collider class (Collide.js)
 * 
 * <https://github.com/AntoineLandrieux/PxEngine>
 */

export class Collider {

    /**
     * @type {number[][]}
     */
    data = [];

    /**
     * Collider class
     */
    constructor() { }

    /**
     * Clear data
     */
    clear() {

        this.data = [];

    }

    /**
     * Record a new collision
     * @param {number} x Position
     * @param {number} y Position
     * @param {number} width Width
     * @param {number} height Height
     * @returns {number}
     */
    Register(x, y, width, height) {

        return this.data.push([x, y, width, height]);

    }

    /**
     * Check if there is a collision
     * @param {number} dx Position
     * @param {number} dy Position
     * @param {number} width Width
     * @param {number} height Height
     * @returns {boolean}
     */
    IsCollide(dx, dy, width, height) {

        let collide = false;

        this.data.every(item => {

            let [x, y, w, h] = item;
            if (dx < x + w && dx + width > x && dy < y + h && dy + height > y)
                collide = true;
            return !collide;

        });

        return collide;

    }

}
