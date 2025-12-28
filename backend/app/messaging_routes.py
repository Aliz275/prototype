from flask import request, jsonify, session
from flask_socketio import emit, join_room, leave_room
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, Conversation, ConversationParticipant, Message, MessageReadStatus
from .auth import role_required
from datetime import datetime

def init_messaging_routes(app, socketio):
    @app.route('/api/conversations', methods=['POST'])
    @role_required(['employee', 'manager', 'admin'])
    def create_conversation():
        db: Session = next(get_db())
        data = request.get_json()
        participant_ids = data.get('participant_ids')
        user = db.query(User).filter(User.email == session.get('email')).first()

        if not participant_ids:
            return jsonify({'message': 'Participant IDs are required'}), 400

        participant_ids.append(user.id)
        participant_ids = list(set(participant_ids))

        is_group_chat = len(participant_ids) > 2
        
        if is_group_chat and user.role not in ['manager', 'admin']:
            return jsonify({'message': 'Only managers and admins can create group chats'}), 403
            
        name = data.get('name') if is_group_chat else None

        new_conversation = Conversation(name=name, is_group_chat=is_group_chat, created_by_id=user.id)
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)

        for participant_id in participant_ids:
            participant = ConversationParticipant(conversation_id=new_conversation.id, user_id=participant_id)
            db.add(participant)
        db.commit()

        return jsonify({'message': 'Conversation created successfully', 'conversation_id': new_conversation.id}), 201

    @app.route('/api/conversations', methods=['GET'])
    @role_required(['employee', 'manager', 'admin'])
    def get_conversations():
        db: Session = next(get_db())
        user = db.query(User).filter(User.email == session.get('email')).first()
        conversations = db.query(Conversation).join(ConversationParticipant).filter(ConversationParticipant.user_id == user.id).all()
        
        conversation_list = []
        for conv in conversations:
            conversation_list.append({
                'id': conv.id,
                'name': conv.name,
                'is_group_chat': conv.is_group_chat
            })
        return jsonify(conversation_list), 200

    @app.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
    @role_required(['employee', 'manager', 'admin'])
    def get_messages(conversation_id):
        db: Session = next(get_db())
        user = db.query(User).filter(User.email == session.get('email')).first()
        participant = db.query(ConversationParticipant).filter(
            (ConversationParticipant.conversation_id == conversation_id) & (ConversationParticipant.user_id == user.id)
        ).first()
        if not participant:
            return jsonify({'message': 'Not a participant of this conversation'}), 403
        
        messages = db.query(Message).filter(
            (Message.conversation_id == conversation_id) & (Message.is_deleted == False)
        ).order_by(Message.created_at.asc()).all()
        
        participant.last_read_timestamp = datetime.utcnow()
        db.commit()
        
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg.id,
                'content': msg.content,
                'created_at': msg.created_at.isoformat(),
                'sender_email': msg.sender.email
            })
        return jsonify(message_list), 200

    @app.route('/api/conversations/<int:conversation_id>/messages', methods=['POST'])
    @role_required(['employee', 'manager', 'admin'])
    def send_message(conversation_id):
        db: Session = next(get_db())
        data = request.get_json()
        content = data.get('content')
        user = db.query(User).filter(User.email == session.get('email')).first()

        participant = db.query(ConversationParticipant).filter(
            (ConversationParticipant.conversation_id == conversation_id) & (ConversationParticipant.user_id == user.id)
        ).first()
        if not participant:
            return jsonify({'message': 'Not a participant of this conversation'}), 403

        new_message = Message(conversation_id=conversation_id, sender_id=user.id, content=content)
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        socketio.emit('new_message', {
            'conversation_id': conversation_id, 
            'message': {
                'id': new_message.id, 
                'content': new_message.content, 
                'sender_email': user.email, 
                'created_at': new_message.created_at.isoformat()
            }
        }, room=f'conversation_{conversation_id}')
        return jsonify({'message': 'Message sent successfully'}), 201

    @app.route('/api/messages/<int:message_id>', methods=['DELETE'])
    @role_required(['employee', 'manager', 'admin'])
    def delete_message(message_id):
        db: Session = next(get_db())
        user = db.query(User).filter(User.email == session.get('email')).first()
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return jsonify({'message': 'Message not found'}), 404

        conversation = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
        
        if user.id == message.sender_id or (user.role in ['manager', 'admin'] and conversation.is_group_chat):
            message.is_deleted = True
            db.commit()
            socketio.emit('message_deleted', {'message_id': message_id, 'conversation_id': message.conversation_id}, room=f'conversation_{message.conversation_id}')
            return jsonify({'message': 'Message deleted successfully'}), 200
        else:
            return jsonify({'message': 'Unauthorized to delete this message'}), 403

    @app.route('/api/messages/<int:message_id>', methods=['PUT'])
    @role_required(['employee', 'manager', 'admin'])
    def edit_message(message_id):
        db: Session = next(get_db())
        data = request.get_json()
        content = data.get('content')
        user = db.query(User).filter(User.email == session.get('email')).first()
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return jsonify({'message': 'Message not found'}), 404
        
        if user.id != message.sender_id:
            return jsonify({'message': 'You can only edit your own messages'}), 403

        message.content = content
        message.updated_at = datetime.utcnow()
        db.commit()
        socketio.emit('message_edited', {'message_id': message_id, 'conversation_id': message.conversation_id, 'content': content}, room=f'conversation_{message.conversation_id}')
        return jsonify({'message': 'Message edited successfully'}), 200

    @app.route('/api/conversations/<int:conversation_id>/participants', methods=['POST'])
    @role_required(['manager', 'admin'])
    def add_participant(conversation_id):
        db: Session = next(get_db())
        data = request.get_json()
        user_id = data.get('user_id')
        
        participant = ConversationParticipant(conversation_id=conversation_id, user_id=user_id)
        db.add(participant)
        db.commit()
        return jsonify({'message': 'Participant added successfully'}), 201

    @app.route('/api/conversations/<int:conversation_id>/participants/<int:user_id>', methods=['DELETE'])
    @role_required(['manager', 'admin'])
    def remove_participant(conversation_id, user_id):
        db: Session = next(get_db())
        participant = db.query(ConversationParticipant).filter(
            (ConversationParticipant.conversation_id == conversation_id) & (ConversationParticipant.user_id == user_id)
        ).first()
        if participant:
            db.delete(participant)
            db.commit()
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
        user = db.query(User).filter(User.email == session.get('email')).first()
        if user:
            emit('user_status', {'user_id': user.id, 'status': 'online'}, broadcast=True)

    @socketio.on('disconnect')
    def on_disconnect():
        user = db.query(User).filter(User.email == session.get('email')).first()
        if user:
            emit('user_status', {'user_id': user.id, 'status': 'offline'}, broadcast=True)

    @socketio.on('read_message')
    def on_read_message(data):
        db: Session = next(get_db())
        user = db.query(User).filter(User.email == session.get('email')).first()
        message_id = data.get('message_id')
        conversation_id = data.get('conversation_id')
        if user and message_id:
            read_status = MessageReadStatus(message_id=message_id, user_id=user.id)
            db.add(read_status)
            try:
                db.commit()
                emit('message_read', {'user_id': user.id, 'message_id': message_id}, room=f'conversation_{conversation_id}')
            except:
                db.rollback()
    
    @app.route('/api/search/messages', methods=['GET'])
    @role_required(['employee', 'manager', 'admin'])
    def search_messages():
        db: Session = next(get_db())
        query = request.args.get('q')
        user = db.query(User).filter(User.email == session.get('email')).first()

        messages = db.query(Message).join(ConversationParticipant).filter(
            (ConversationParticipant.user_id == user.id) & (Message.content.ilike(f'%{query}%')) & (Message.is_deleted == False)
        ).order_by(Message.created_at.desc()).all()

        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg.id,
                'content': msg.content,
                'created_at': msg.created_at.isoformat(),
                'sender_email': msg.sender.email,
                'conversation_id': msg.conversation_id
            })
        return jsonify(message_list)
