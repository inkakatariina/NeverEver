// Connect to Socket.IO server
const socket = io();
const roomId = document.getElementById('roomId')?.value || new URLSearchParams(window.location.search).get('room');
let currentUsername = '';

// Home Page Functions
function createRoom() {
    fetch('/api/create-room', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        window.location.href = `/game/${data.room_id}`;
    });
}

function joinRoom() {
    const roomCode = document.getElementById('roomCode').value.toUpperCase();
    if (roomCode) {
        window.location.href = `/game/${roomCode}`;
    }
}

// Game Page Functions
function joinGame() {
    const usernameInput = document.getElementById('username');
    const username = usernameInput.value.trim();
    
    if (username && roomId) {
        currentUsername = username;
        document.getElementById('joinForm').style.display = 'none';
        document.getElementById('waitingRoom').style.display = 'block';
        
        socket.emit('join', {
            username: username,
            room: roomId
        });
    }
}

function startGame() {
    socket.emit('start_game', {
        room: roomId
    });
}

function nextQuestion() {
    socket.emit('next_question', {
        room: roomId
    });
}

// Socket.IO Event Handlers
socket.on('room_update', (data) => {
    const playersList = document.getElementById('playersList');
    if (playersList) {
        playersList.innerHTML = '';
        data.players.forEach(player => {
            const li = document.createElement('li');
            li.textContent = player;
            playersList.appendChild(li);
        });
    }
});

socket.on('joined', (data) => {
    const notificationArea = document.getElementById('notifications');
    if (notificationArea) {
        const message = document.createElement('p');
        message.textContent = `${data.username} has joined the room!`;
        notificationArea.appendChild(message);
    }
});

socket.on('player_left', (data) => {
    const notificationArea = document.getElementById('notifications');
    if (notificationArea) {
        const message = document.createElement('p');
        message.textContent = `${data.username} has left the room.`;
        notificationArea.appendChild(message);
    }
});

socket.on('game_started', () => {
    document.getElementById('waitingRoom').style.display = 'none';
    document.getElementById('gameArea').style.display = 'block';
});

socket.on('new_question', (data) => {
    document.getElementById('questionText').textContent = data.question;
    document.getElementById('questionCounter').textContent = 
        `Question ${data.question_number} of ${data.total_questions}`;
    
    // Reset any UI state for the new question
    document.getElementById('nextQuestionBtn').style.display = 'block';
});

socket.on('game_over', () => {
    document.getElementById('gameArea').style.display = 'none';
    document.getElementById('gameOver').style.display = 'block';
});

socket.on('error', (data) => {
    alert(data.message);
});

// Add event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Home page buttons
    const createRoomBtn = document.getElementById('createRoomBtn');
    if (createRoomBtn) {
        createRoomBtn.addEventListener('click', createRoom);
    }
    
    const joinRoomBtn = document.getElementById('joinRoomBtn');
    if (joinRoomBtn) {
        joinRoomBtn.addEventListener('click', joinRoom);
    }
    
    // Game page buttons
    const joinGameBtn = document.getElementById('joinGameBtn');
    if (joinGameBtn) {
        joinGameBtn.addEventListener('click', joinGame);
    }
    
    const startGameBtn = document.getElementById('startGameBtn');
    if (startGameBtn) {
        startGameBtn.addEventListener('click', startGame);
    }
    
    const nextQuestionBtn = document.getElementById('nextQuestionBtn');
    if (nextQuestionBtn) {
        nextQuestionBtn.addEventListener('click', nextQuestion);
    }
});
