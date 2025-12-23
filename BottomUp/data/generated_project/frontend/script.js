const display = document.getElementById('display');
const buttons = document.querySelectorAll('.buttons button');

let currentNumber = '';
let previousNumber = '';
let operator = '';

buttons.forEach(button => {
    button.addEventListener('click', () => {
        const value = button.dataset;
        if (value.number) {
            currentNumber += value.number;
            display.value = currentNumber;
        } else if (value.operator) {
            previousNumber = currentNumber;
            currentNumber = '';
            operator = value.operator;
            display.value = previousNumber + ' ' + operator;
        } else if (value.equals) {
            if (operator === '+') {
                display.value = parseFloat(previousNumber) + parseFloat(currentNumber);
            } else if (operator === '-') {
                display.value = parseFloat(previousNumber) - parseFloat(currentNumber);
            } else if (operator === '*') {
                display.value = parseFloat(previousNumber) * parseFloat(currentNumber);
            } else if (operator === '/') {
                display.value = parseFloat(previousNumber) / parseFloat(currentNumber);
            }
            currentNumber = display.value;
            previousNumber = '';
            operator = '';
        } else if (value.clear) {
            currentNumber = '';
            display.value = '';
        }
    });
});