const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/'
);

const chatLog = document.getElementById('chat-log');
const messageInput = document.getElementById('chat-message-input');
const submitButton = document.getElementById('chat-message-submit');

chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message agent-message';
    messageDiv.innerText = data.message;
    chatLog.appendChild(messageDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
};

chatSocket.onclose = function (e) {
    console.error('WebSocket закрився несподівано.');
};

function sendMessage() {
    const message = messageInput.value.trim();
    if (message) {
        const userMsgDiv = document.createElement('div');
        userMsgDiv.className = 'message user-message';
        userMsgDiv.innerText = message;
        chatLog.appendChild(userMsgDiv);
        chatLog.scrollTop = chatLog.scrollHeight;

        chatSocket.send(JSON.stringify({
            'message': message
        }));
        messageInput.value = '';
    }
}

messageInput.onkeyup = function (e) {
    if (e.keyCode === 13) {
        sendMessage();
    }
};

submitButton.onclick = sendMessage;
