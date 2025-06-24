
/* Last action */
let LastAction = null;

/**
 * Returns last action
 * @returns {string|null}
 */
export function getLastAction() {

    return LastAction;

}

/**
 * Sets last action to null
 */
export function clearLastAction() {

    LastAction = null;

}

window.addEventListener("keyup", (event) => {

    switch (event.key.toLowerCase()) {

        case "escape":
        case "enter":

            LastAction = event.key.toLowerCase();

        default:

            break;

    }

});

window.addEventListener("keydown", (event) => {

    switch (event.key.toLowerCase()) {

        case "arrowup":
        case "arrowleft":
        case "arrowdown":
        case "arrowright":

            LastAction = event.key.toLowerCase();

        default:

            break;

    }

});
