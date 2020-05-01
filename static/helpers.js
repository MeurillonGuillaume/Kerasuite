const Get8bitValue = () => {
    /**
     * Request a random value between 1-255
     */
    return Math.floor((Math.random() * 255) + 1)
}

const GetRandomColor = (opacity = 0.75) => {
    /**
     * Request a random RGBA color-String
     * @param {number} opacity: The opacity of the color
     */
    return `rgba(${Get8bitValue()},${Get8bitValue()},${Get8bitValue()}, ${opacity})`
}

const GetRandomColors = (amount) => {
    /**
     * Request an array of random colors
     * @param   {String}    amount   The amount of colors to generate
     */
    let result = [];
    for (let i = 0; i < amount; i++) {
        result.push(GetRandomColor());
    }
    return result;
}