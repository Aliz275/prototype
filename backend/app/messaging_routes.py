from flask import request, jsonify, session
from flask_socketio import emit, join_room, leave_room
from app.auth import role_required
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

def init_messaging_routes(app, socketio):
    @app.route('/api/conversations', methods=['POST'])
    @role_required(['employee', 'manager', 'admin'])
    def create_conversation():
        data = request.get_json()
        participant_ids = data.get('participant_ids')
        user_id = session.get('user_id')

        if not participant_ids:
            return jsonify({'message': 'Participant IDs are required'}), 400

        participant_ids.append(user_id)
        # remove duplicates
        participant_ids = list(set(participant_ids))

        is_group_chat = len(participant_ids) > 2
        name = data.get('name') if is_group_chat else None

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO conversations (name, is_group_chat, created_by_id) VALUES (?, ?, ?)", (name, is_group_chat, user_id))
        conversation_id = c.lastrowid
        for participant_id in participant_ids:
            c.execute("INSERT INTO conversation_participants (conversation_id, user_id) VALUES (?, ?)", (conversation_id, participant_id))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Conversation created successfully', 'conversation_id': conversation_id}), 201

    @app.route('/api/conversations', methods=['GET'])
    @role_required(['employee', 'manager', 'admin'])
    def get_conversations():
        user_id = session.get('user_id')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT c.id, c.name, c.is_group_chat
            FROM conversations c
            JOIN conversation_participants cp ON c.id = cp.conversation_id
            WHERE cp.user_id = ?
        """, (user_id,))
        conversations = c.fetchall()
        conn.close()
        return jsonify(conversations), 200

    @app.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
    @role_required(['employee', 'manager', 'admin'])
    def get_messages(conversation_id):
        user_id = session.get('user_id')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id FROM conversation_participants WHERE conversation_id = ? AND user_id = ?", (conversation_id, user_id))
        participant = c.fetchone()
        if not participant:
            return jsonify({'message': 'Not a participant of this conversation'}), 403
        
        c.execute("""
            SELECT m.id, m.content, m.created_at, u.email as sender_email
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.conversation_id = ? AND m.is_deleted = 0
            ORDER BY m.created_at ASC
        """, (conversation_id,))
        messages = c.fetchall()
        
        # Update last_read_timestamp
        c.execute("UPDATE conversation_participants SET last_read_timestamp = ? WHERE conversation_id = ? AND user_id = ?", (datetime.utcnow(), conversation_id, user_id))
        conn.commit()
        
        conn.close()
        return jsonify(messages), 200

    @app.route('/api/conversations/<int:conversation_id>/messages', methods=['POST'])
    @role_required(['employee', 'manager', 'admin'])
    def send_message(conversation_id):
        data = request.get_json()
        content = data.get('content')
        user_id = session.get('user_id')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id FROM conversation_participants WHERE conversation_id = ? AND user_id = ?", (conversation_id, user_id))
        participant = c.fetchone()
        if not participant:
            return jsonify({'message': 'Not a participant of this conversation'}), 403

        c.execute("INSERT INTO messages (conversation_id, sender_id, content) VALUES (?, ?, ?)", (conversation_id, user_id, content))
        message_id = c.lastrowid
        conn.commit()
        c.execute("SELECT created_at FROM messages WHERE id = ?", (message_id,))
        created_at = c.fetchone()[0]
        conn.close()
        
        c.execute("SELECT u.email FROM users u WHERE u.id = ?", (user_id,))
        sender_email = c.fetchone()[0]


        socketio.emit('new_message', {'conversation_id': conversation_id, 'message': {'id': message_id, 'content': content, 'sender_email': sender_email, 'created_at': created_at}}, room=f'conversation_{conversation_id}')
        return jsonify({'message': 'Message sent successfully'}), 201
    
    @socketio.on('join')
    def on_join(data):
        conversation_id = data['conversation_id']
        join_room(f'conversation_{conversation_id}')

    @socketio.on('leave')
    def on_leave(data):
        conversation_id = data['conversation_id']
        leave_room(f'conversation_{conversation_id}')
