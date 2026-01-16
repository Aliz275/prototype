from flask import request, jsonify, session
from flask_socketio import emit, join_room, leave_room
from app.auth import role_required, get_current_user
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

def init_messaging_routes(app, socketio):
    @app.route('/api/conversations', methods=['POST'])
    @role_required(['employee', 'manager', 'admin', 'super_admin'])
    def create_conversation():
        user_id, user_role, user_organization_id = get_current_user()
        if not user_id:
            return jsonify({'message': 'Unauthorized'}), 401

        data = request.get_json()
        participant_ids = data.get('participant_ids')

        if not participant_ids:
            return jsonify({'message': 'Participant IDs are required'}), 400

        participant_ids.append(user_id)
        participant_ids = list(set(participant_ids))

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Authorization checks
        if user_role == 'employee':
            for pid in participant_ids:
                c.execute('SELECT organization_id FROM users WHERE id = ?', (pid,))
                org_id = c.fetchone()
                if not org_id or org_id[0] != user_organization_id:
                    conn.close()
                    return jsonify({'message': 'Employees can only message users within their own organization.'}), 403
        elif user_role == 'team_manager':
            # Check if all participants are in the same org or are team managers
            for pid in participant_ids:
                c.execute('SELECT organization_id, role FROM users WHERE id = ?', (pid,))
                p_info = c.fetchone()
                if not p_info or (p_info[0] != user_organization_id and p_info[1] != 'team_manager'):
                    conn.close()
                    return jsonify({'message': 'Team managers can only message users in their org or other team managers.'}), 403
        elif user_role == 'org_admin':
            # Check if all participants are in the same org or are org admins
            for pid in participant_ids:
                c.execute('SELECT organization_id, role FROM users WHERE id = ?', (pid,))
                p_info = c.fetchone()
                if not p_info or (p_info[0] != user_organization_id and p_info[1] != 'org_admin'):
                    conn.close()
                    return jsonify({'message': 'Org admins can only message users in their org or other org admins.'}), 403

        is_group_chat = len(participant_ids) > 2

        if is_group_chat and user_role not in ['manager', 'admin', 'super_admin']:
            conn.close()
            return jsonify({'message': 'Only managers and admins can create group chats'}), 403

        name = data.get('name') if is_group_chat else None

        c.execute("INSERT INTO conversations (name, is_group_chat, created_by_id) VALUES (?, ?, ?)", (name, is_group_chat, user_id))
        conversation_id = c.lastrowid
        for participant_id in participant_ids:
            c.execute("INSERT INTO conversation_participants (conversation_id, user_id) VALUES (?, ?)", (conversation_id, participant_id))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Conversation created successfully', 'conversation_id': conversation_id}), 201

    @app.route('/api/conversations', methods=['GET'])
    @role_required(['employee', 'manager', 'admin', 'super_admin'])
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
    @role_required(['employee', 'manager', 'admin', 'super_admin'])
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
    @role_required(['employee', 'manager', 'admin', 'super_admin'])
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

    @app.route('/api/messages/<int:message_id>', methods=['DELETE'])
    @role_required(['employee', 'manager', 'admin', 'super_admin'])
    def delete_message(message_id):
        user_id, user_role, _ = get_current_user()
        if not user_id:
            return jsonify({'message': 'Unauthorized'}), 401

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT sender_id, conversation_id FROM messages WHERE id = ?", (message_id,))
        message = c.fetchone()
        if not message:
            conn.close()
            return jsonify({'message': 'Message not found'}), 404

        sender_id, conversation_id = message

        c.execute("SELECT is_group_chat FROM conversations WHERE id = ?", (conversation_id,))
        conversation = c.fetchone()
        is_group_chat = conversation[0]

        can_delete = False
        if user_id == sender_id:
            can_delete = True
        elif user_role in ['manager', 'admin', 'super_admin'] and is_group_chat:
            c.execute("SELECT 1 FROM conversation_participants WHERE user_id = ? AND conversation_id = ?", (user_id, conversation_id))
            is_participant = c.fetchone()
            if is_participant:
                can_delete = True

        if can_delete:
            c.execute("UPDATE messages SET is_deleted = 1 WHERE id = ?", (message_id,))
            conn.commit()
            socketio.emit('message_deleted', {'message_id': message_id, 'conversation_id': conversation_id}, room=f'conversation_{conversation_id}')
            return jsonify({'message': 'Message deleted successfully'}), 200
        else:
            conn.close()
            return jsonify({'message': 'Unauthorized to delete this message'}), 403

    @app.route('/api/messages/<int:message_id>', methods=['PUT'])
    @role_required(['employee', 'manager', 'admin', 'super_admin'])
    def edit_message(message_id):
        data = request.get_json()
        content = data.get('content')
        user_id = session.get('user_id')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT sender_id, conversation_id FROM messages WHERE id = ?", (message_id,))
        message = c.fetchone()
        if not message:
            conn.close()
            return jsonify({'message': 'Message not found'}), 404

        sender_id, conversation_id = message

        if user_id != sender_id:
            conn.close()
            return jsonify({'message': 'You can only edit your own messages'}), 403

        c.execute("UPDATE messages SET content = ?, updated_at = ? WHERE id = ?", (content, datetime.utcnow(), message_id))
        conn.commit()
        conn.close()
        socketio.emit('message_edited', {'message_id': message_id, 'conversation_id': conversation_id, 'content': content}, room=f'conversation_{conversation_id}')
        return jsonify({'message': 'Message edited successfully'}), 200

    @app.route('/api/conversations/<int:conversation_id>/participants', methods=['POST'])
    @role_required(['manager', 'admin', 'super_admin'])
    def add_participant(conversation_id):
        data = request.get_json()
        user_id = data.get('user_id')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO conversation_participants (conversation_id, user_id) VALUES (?, ?)", (conversation_id, user_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Participant added successfully'}), 201

    @app.route('/api/conversations/<int:conversation_id>/participants/<int:user_id>', methods=['DELETE'])
    @role_required(['manager', 'admin', 'super_admin'])
    def remove_participant(conversation_id, user_id):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM conversation_participants WHERE conversation_id = ? AND user_id = ?", (conversation_id, user_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Participant removed successfully'}), 200

    @socketio.on('join')
    def on_join(data):
        conversation_id = data['conversation_id']
        join_room(f'conversation_{conversation_id}')

    @socketio.on('leave')
    def on_leave(data):
        conversation_id = data['conversation_id']
        leave_room(f'conversation_{conversation_id}')

    @socketio.on('connect')
    def on_connect():
        user_id = session.get('user_id')
        if user_id:
            # Broadcast to other users that this user is online
            emit('user_status', {'user_id': user_id, 'status': 'online'}, broadcast=True)

    @socketio.on('disconnect')
    def on_disconnect():
        user_id = session.get('user_id')
        if user_id:
            # Broadcast to other users that this user is offline
            emit('user_status', {'user_id': user_id, 'status': 'offline'}, broadcast=True)

    @socketio.on('read_message')
    def on_read_message(data):
        user_id = session.get('user_id')
        message_id = data.get('message_id')
        conversation_id = data.get('conversation_id')
        if user_id and message_id:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO message_read_status (message_id, user_id) VALUES (?, ?)", (message_id, user_id))
                conn.commit()
                # Notify others in the conversation that the message has been read
                emit('message_read', {'user_id': user_id, 'message_id': message_id}, room=f'conversation_{conversation_id}')
            except sqlite3.IntegrityError:
                # The user has already read this message
                pass
            finally:
                conn.close()

    @app.route('/api/search/messages', methods=['GET'])
    @role_required(['employee', 'manager', 'admin', 'super_admin'])
    def search_messages():
        query = request.args.get('q')
        user_id = session.get('user_id')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT m.id, m.content, m.created_at, u.email as sender_email, c.id as conversation_id
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            JOIN conversations c ON m.conversation_id = c.id
            JOIN conversation_participants cp ON c.id = cp.conversation_id
            WHERE cp.user_id = ? AND m.content LIKE ? AND m.is_deleted = 0
            ORDER BY m.created_at DESC
        """, (user_id, f'%{query}%'))
        messages = c.fetchall()
        conn.close()

        return jsonify(messages)