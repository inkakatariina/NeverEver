// Game variables
let gameId = null;
let playerId = null;
let isHost = false;
let socket = null;
let hasAnswered = false;
let currentQuestionId = null;
let waitingArea, questionArea, answersArea, actionButtons;
let currentQuestionElement, answersList, answerYesBtn, answerNoBtn, nextQuestionBtn;
let currentQuestion = null;
let questionCounter = 0;
let totalQuestions = 0;

// Get URL parameters function
function getUrlParams() {
  const params = new URLSearchParams(window.location.search);
  return {
    gameId: params.get('game'),
    playerId: params.get('player'),
    isHost: params.get('host') === 'true'
  };
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  // Get DOM elements
  waitingArea = document.getElementById('waiting-area');
  questionArea = document.getElementById('question-area');
  answersArea = document.getElementById('answers-area');
  actionButtons = document.getElementById('action-buttons');
  currentQuestionElement = document.getElementById('current-question');
  answersList = document.getElementById('answers-list');
  answerYesBtn = document.getElementById('answer-yes');
  answerNoBtn = document.getElementById('answer-no');
  nextQuestionBtn = document.getElementById('next-question');
  
  // Get game parameters from URL
  const params = getUrlParams();
  gameId = params.gameId;
  playerId = params.playerId;
  isHost = params.isHost;
  
  if (!gameId) {
    showError('No game ID provided');
    return;
  }
  
  if (!playerId) {
    showError('No player ID provided');
    return;
  }
  
  // Setup page based on player role
  if (isHost) {
    document.getElementById('host-controls').classList.remove('hidden');
    nextQuestionBtn.classList.remove('hidden');
  } else {
    document.getElementById('host-controls').classList.add('hidden');
    nextQuestionBtn.classList.add('hidden');
  }
  
  // Initialize socket connection
  initializeSocketConnection();
  
  // Fetch game info
  fetchGameInfo(gameId, playerId);
  
  // Setup event listeners
  setupEventListeners();
});

// Initialize Socket.IO connection
function initializeSocketConnection() {
  console.log("Initializing socket connection");
  
  // Initialize Socket.IO connection
  socket = io.connect(window.location.origin, {
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
  });
  
  // Set up socket event handlers
  socket.on('connect', () => {
    console.log('Socket connected');
    showNotification("Connected to game server", "success");
    
    // Join the game room
    socket.emit('join_game', {
      game_id: gameId,
      player_id: playerId
    });
  });
  
  socket.on('join_success', (data) => {
    console.log('Successfully joined game:', data);
    updatePlayerList(data.players);
  });
  
  socket.on('player_joined', (data) => {
    console.log('Player joined:', data);
    showNotification(`${data.player.name} joined the game`, 'info');
    updatePlayerList(data.players);
  });
  
  socket.on('game_started', (data) => {
    console.log('Game started:', data);
    // Hide waiting area, show question area
    waitingArea.classList.add('hidden');
    questionArea.classList.remove('hidden');
    
    // Display first question
    const questionObj = data.question;
    currentQuestionElement.textContent = "Never have I ever " + questionObj.text;
    currentQuestion = questionObj;
    currentQuestionId = questionObj.id;
    questionCounter = 1;
    
    // Reset answer state
    hasAnswered = false;
    answerYesBtn.disabled = false;
    answerNoBtn.disabled = false;
    answerYesBtn.classList.remove('selected');
    answerNoBtn.classList.remove('selected');
    
    // Clear answers list
    answersList.innerHTML = '';
    
    // Hide answers area until people answer
    answersArea.classList.add('hidden');
  });
  
  socket.on('answer_submitted', (data) => {
    console.log('Answer submitted:', data);
    updateAnswersList(data.all_answers);
  });
  
  socket.on('new_question', (data) => {
    console.log('New question:', data);
    // Display new question
    const questionObj = data.question;
    currentQuestionElement.textContent = "Never have I ever " + questionObj.text;
    currentQuestion = questionObj;
    currentQuestionId = questionObj.id;
    questionCounter++;
    
    // Reset answer state
    hasAnswered = false;
    answerYesBtn.disabled = false;
    answerNoBtn.disabled = false;
    answerYesBtn.classList.remove('selected');
    answerNoBtn.classList.remove('selected');
    
    // Clear answers list
    answersList.innerHTML = '';
    
    // Hide answers area until people answer
    answersArea.classList.add('hidden');
  });
  
  socket.on('game_over', () => {
    console.log('Game over');
    showNotification("Game over! You've gone through all the questions.", "info");
    currentQuestionElement.textContent = "Game Over! Thanks for playing!";
    answerYesBtn.disabled = true;
    answerNoBtn.disabled = true;
    nextQuestionBtn.disabled = true;
  });
  
  socket.on('error', (data) => {
    console.error('Socket error:', data);
    showError(data.message || 'An error occurred');
  });
  
  socket.on('disconnect', () => {
    console.log('Socket disconnected');
    showNotification("Disconnected from game server", "warning");
  });
}

// Fetch game info from the server
function fetchGameInfo(gameId, playerId) {
  // Get game details
  fetch(`/api/games/${gameId}`)
    .then(response => {
      if (!response.ok) {
        throw new Error('Game not found');
      }
      return response.json();
    })
    .then(gameData => {
      console.log('Game data:', gameData);
      
      // Set game title
      const modeStr = gameData.game_modes && gameData.game_modes.includes(',') ? 
                      'Mixed Categories' : 
                      (gameData.game_modes || 'Mixed Categories');
      
      document.getElementById('game-title').textContent = `Never Have I Ever: ${modeStr}`;
      
      // Update player list
      updatePlayerList(gameData.players);
      
      // Get game questions to know the total
      return fetch(`/api/games/${gameId}/questions`);
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to fetch questions');
      }
      return response.json();
    })
    .then(questions => {
      console.log('Questions count:', questions.length);
      totalQuestions = questions.length;
    })
    .catch(error => {
      console.error('Error fetching game info:', error);
      showError(error.message);
    });
}

// Setup event listeners
function setupEventListeners() {
  // Answer buttons
  answerYesBtn.addEventListener('click', () => {
    submitAnswer(true);
  });
  
  answerNoBtn.addEventListener('click', () => {
    submitAnswer(false);
  });
  
  // Next question button (host only)
  nextQuestionBtn.addEventListener('click', () => {
    moveToNextQuestion();
  });
  
  // Start game button (host only)
  document.getElementById('start-game-btn').addEventListener('click', () => {
    startGame();
  });
}

// Show a notification message
function showNotification(message, type = 'success') {
  const notification = document.getElementById('notification');
  notification.textContent = message;
  notification.className = 'notification'; // Reset classes
  notification.classList.add(type);
  notification.classList.remove('hidden');
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    notification.classList.add('hidden');
  }, 5000);
}

// Show an error message
function showError(message) {
  showNotification(message, 'error');
}

// Update the player list
function updatePlayerList(players) {
  const playersList = document.getElementById('players-list');
  if (!playersList) return;
  
  playersList.innerHTML = '';
  
  players.forEach(player => {
    const li = document.createElement('li');
    li.textContent = player.name + (player.is_host ? ' (Host)' : '');
    playersList.appendChild(li);
  });
  
  // Update player count
  document.getElementById('player-count').textContent = players.length;
}

// Start the game (host only)
function startGame() {
  if (!isHost) {
    showError('Only the host can start the game');
    return;
  }
  
  socket.emit('start_game', {
    game_id: gameId,
    player_id: playerId
  });
}

// Submit an answer to the current question
function submitAnswer(answer) {
  if (hasAnswered) {
    return;
  }
  
  if (!currentQuestionId) {
    showError('No active question');
    return;
  }
  
  // Highlight selected button
  if (answer) {
    answerYesBtn.classList.add('selected');
    answerNoBtn.classList.remove('selected');
  } else {
    answerYesBtn.classList.remove('selected');
    answerNoBtn.classList.add('selected');
  }
  
  // Mark as answered
  hasAnswered = true;
  answerYesBtn.disabled = true;
  answerNoBtn.disabled = true;
  
  // Send answer to server
  socket.emit('submit_answer', {
    game_id: gameId,
    player_id: playerId,
    question_id: currentQuestionId,
    answer: answer
  });
}

// Update the answers list
function updateAnswersList(answers) {
  answersList.innerHTML = '';
  
  const yesAnswers = answers.filter(a => a.answer);
  const noAnswers = answers.filter(a => !a.answer);
  
  // Create "I have" group
  const yesGroup = document.createElement('div');
  yesGroup.className = 'answer-group yes-answers';
  yesGroup.innerHTML = '<h3>I Have:</h3>';
  const yesUl = document.createElement('ul');
  
  yesAnswers.forEach(answer => {
    const li = document.createElement('li');
    li.textContent = answer.player_name;
    yesUl.appendChild(li);
  });
  
  yesGroup.appendChild(yesUl);
  answersList.appendChild(yesGroup);
  
  // Create "I have not" group
  const noGroup = document.createElement('div');
  noGroup.className = 'answer-group no-answers';
  noGroup.innerHTML = '<h3>I Have Not:</h3>';
  const noUl = document.createElement('ul');
  
  noAnswers.forEach(answer => {
    const li = document.createElement('li');
    li.textContent = answer.player_name;
    noUl.appendChild(li);
  });
  
  noGroup.appendChild(noUl);
  answersList.appendChild(noGroup);
  
  // Show answers area
  answersArea.classList.remove('hidden');
}

// Move to the next question (host only)
function moveToNextQuestion() {
  if (!isHost) {
    showError('Only the host can move to the next question');
    return;
  }
  
  if (!currentQuestionId) {
    showError('No active question');
    return;
  }
  
  socket.emit('next_question', {
    game_id: gameId,
    player_id: playerId,
    current_question_id: currentQuestionId
  });
}