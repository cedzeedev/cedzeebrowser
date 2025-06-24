import { WIDTH } from "../Context.js";

export class Pokemon {

    /**
     * 
     * @param {CanvasImageSource} sprite 
     * @param {CanvasRenderingContext2D} context 
     * @param {string} name 
     * @param {number} health 
     * @param {number} xp 
     */
    constructor(

        sprite,
        context,
        name,
        health = 20 + Math.floor(Math.random() * 10),
        xp = 20 + Math.floor(Math.random() * 100)

    ) {

        this.sprite = sprite;
        this.name = name;
        this.context = context;

        this.max_health = this.health = health;
        this.xp = 0;
        this.level = 1;

        this.AddXP(xp);

    }

    /**
     * 
     * @returns {number}
     */
    #__get_next_level() {

        return 90 * this.level;

    }

    /**
     * 
     * @param {string} top 
     */
    Hub(top = "left") {

        this.context.font = "20px PokemonClassic"

        this.context.fillStyle = "#696969";
        this.context.fillRect(top == "right" ? WIDTH - 310 - 15 : 10, 10, 310, 135);

        this.context.fillStyle = "#dadada";
        this.context.fillRect(top == "right" ? WIDTH - 310 - 10 : 15, 15, 300, 125);

        this.context.fillStyle = "#000000";
        this.context.fillText(`${this.name} lvl${this.level}`, top == "right" ? WIDTH - 310 - 5 : 20, 25);

        this.context.fillStyle = "#696969";
        this.context.fillRect(top == "right" ? WIDTH - 310 - 5 : 20, 60, 285, 30);
        this.context.fillStyle = "#ff0000";
        this.context.fillRect(top == "right" ? WIDTH - 310 - 5 : 20, 60, 285 * (this.health / this.max_health), 30);

        this.context.fillStyle = "#000000";
        this.context.fillText(`PV : ${this.health}/${this.max_health}`, top == "right" ? WIDTH - 310 : 25, 65);

        this.context.fillStyle = "#696969";
        this.context.fillRect(top == "right" ? WIDTH - 310 - 5 : 20, 100, 285, 30);
        this.context.fillStyle = "#0000ff";
        this.context.fillRect(top == "right" ? WIDTH - 310 - 5 : 20, 100, 285 * (this.xp / this.#__get_next_level()), 30);

        this.context.fillStyle = "#000000";
        this.context.fillText(`XP : ${this.xp}/${this.#__get_next_level()}`, top == "right" ? WIDTH - 310 : 25, 105)

    }

    /**
     * 
     * @param {number} attack 
     * @returns {number}
     */
    Damage(attack) {

        this.health -= attack;
        this.health = Math.max(0, this.health);
        return this.health;

    }

    /**
     * 
     * @param {number} health 
     * @returns {number}
     */
    Heal(health) {

        this.health += health;
        this.health = Math.min(this.max_health, this.health);
        return this.health;

    }

    /**
     * 
     * @param {number} xp 
     * @returns {number}
     */
    AddXP(xp = 0) {

        this.xp += xp;

        while (this.xp >= this.#__get_next_level()) {

            this.level++;
            this.health = this.max_health += 5 + Math.floor(Math.random() * 5);

        }

        return this.xp;

    }

    /**
     * 
     * @returns {Pokemon}
     */
    Copy() {

        return new Pokemon(this.sprite, this.context, this.name, this.max_health, this.xp);

    }

}
