from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import sqlite3

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Bd
def init_db():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      channel TEXT,
                      sender TEXT,
                      message TEXT,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()


def save_message(channel, sender, message):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (channel, sender, message) VALUES (?, ?, ?)",
                   (channel, sender, message))
    conn.commit()
    conn.close()


def get_messages(channel):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("SELECT sender, message, timestamp FROM messages WHERE channel = ? ORDER BY timestamp", (channel,))
    messages = cursor.fetchall()
    conn.close()
    return messages


@app.route('/')
def index():
    return render_template('index.html')

# sockets
@socketio.on('join')
def handle_join(data):
    username = data['username']
    channel = data['channel']
    join_room(channel)
    user_count = len(socketio.server.manager.rooms['/'].get(channel, []))
    emit('updateUserCount', user_count, room=channel)
    emit('message', {'sender': 'Server', 'message': f'{username} se ha unido al canal {channel}'}, room=channel)

@socketio.on('message')
def handle_message(data):
    username = data['username']
    message = data['message']
    channel = data['channel']
    save_message(channel, username, message)
    emit('message', {'sender': username, 'message': message}, room=channel)

@socketio.on('leave')
def handle_leave(data):
    username = data['username']
    channel = data['channel']
    leave_room(channel)
    user_count = len(socketio.server.manager.rooms['/'].get(channel, []))
    emit('updateUserCount', user_count, room=channel)
    emit('message', {'sender': 'Server', 'message': f'{username} ha salido del canal {channel}'}, room=channel)

# videollamada
@socketio.on('start_call')
def handle_start_call(data):
    channel = data.get('channel')
    if channel:
        emit('incoming_call', data, room=channel, include_self=False)

@socketio.on('offer')
def handle_offer(data):
    channel = data.get('channel')
    if channel:
        emit('offer', data, room=channel, include_self=False)

@socketio.on('answer')
def handle_answer(data):
    channel = data.get('channel')
    if channel:
        emit('answer', data, room=channel, include_self=False)

@socketio.on('candidate')
def handle_candidate(data):
    channel = data.get('channel')
    if channel:
        emit('candidate', data, room=channel, include_self=False)

@socketio.on('endCall')
def handle_end_call(data):
    channel = data.get('channel')
    if channel:
        emit('endCall', room=channel)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)


