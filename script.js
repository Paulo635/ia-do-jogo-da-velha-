const board = document.getElementById("board");
const squares = document.querySelectorAll(".square");
let currentPlayer = "X";
let gameOver = false;
let moves = 0;
let winningCombos = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6],
];

squares.forEach((square) => {
    square.addEventListener("click", () => {
        if (!gameOver && !square.innerText) {
            square.innerText = currentPlayer;
            moves++;
            if (checkForWinner()) {
                alert(`${currentPlayer} ganhou!`);
                gameOver = true;
            } else if (moves === 9) {
                alert("Empate!");
                gameOver = true;
            } else {
                currentPlayer = currentPlayer === "X" ? "O" : "X";
            }
        }
    });
});

function checkForWinner() {
    return winningCombos.some((combo) => {
        return combo.every((index) => {
            return squares[index].innerText === currentPlayer;
        });
    });
}
