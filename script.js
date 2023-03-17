const board = document.getElementById('board');
const squares = document.querySelectorAll('.square');
const winningLines = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
];

let player = 'X';
let gameover = false;

function handleClick(e) {
    if (gameover || e.target.classList.contains('clicked')) {
        return;
    }

    e.target.textContent = player;
    e.target.classList.add('clicked');

    if (checkWin()) {
        alert(`${player} ganhou!`);
        gameover = true;
        return;
    }

    if (checkTie()) {
        alert('Empate!');
        gameover = true;
        return;
    }

    switchPlayer();
    if (player === 'O') {
        setTimeout(makeAiMove, 500);
    }
}

function checkWin() {
    return winningLines.some(line => {
        return line.every(index => {
            return squares[index].textContent === player;
        });
    });
}

function checkTie() {
    return [...squares].every(square => {
        return square.textContent !== '';
    });
}

function switchPlayer() {
    player = player === 'X' ? 'O' :
