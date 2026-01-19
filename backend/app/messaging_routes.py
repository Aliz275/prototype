#backend/app/messaging_routes.py

from flask import request, jsonify, session
from flask_socketio import emit, join_room, leave_room
from app.auth import role_required
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database.db")


def init_messaging_routes(app, socketio):

    # =========================
    # CREATE CONVERSATION
    # =========================
    @app.route("/api/conversations", methods=["POST"])
    @role_required(["employee", "manager", "admin", "super_admin"])
    def create_conversation():
        data = request.get_json() or {}
        participant_ids = data.get("participant_ids", [])
        user_id = session.get("user_id")
        role = session.get("role")

        if not participant_ids:
            return jsonify({"message": "Participants required"}), 400

        participant_ids.append(user_id)
        participant_ids = list(set(participant_ids))
        is_group_chat = len(participant_ids) > 2

        if is_group_chat and role not in ["manager", "admin"]:
            return jsonify({"message": "Only managers/admins can create group chats"}), 403

        name = data.get("name") if is_group_chat else None

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            "INSERT INTO conversations (name, is_group_chat, created_by_id) VALUES (?, ?, ?)",
            (name, is_group_chat, user_id),
        )
        conversation_id = c.lastrowid

        for pid in participant_ids:
            c.execute(
                "INSERT INTO conversation_participants (conversation_id, user_id) VALUES (?, ?)",
                (conversation_id, pid),
            )

        conn.commit()
        conn.close()

        return jsonify({"conversation_id": conversation_id}), 201


    # =========================
    # GET USER CONVERSATIONS
    # =========================
    @app.route("/api/conversations", methods=["GET"])
    @role_required(["employee", "manager", "admin", "super_admin"])
    def get_conversations():
        user_id = session.get("user_id")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            SELECT c.id, c.name, c.is_group_chat
            FROM conversations c
            JOIN conversation_participants cp ON c.id = cp.conversation_id
            WHERE cp.user_id = ?
            ORDER BY c.id DESC
        """, (user_id,))

        rows = c.fetchall()
        conn.close()

        return jsonify([
            {"id": r[0], "name": r[1], "is_group_chat": r[2]}
            for r in rows
        ]), 200


    # =========================
    # CREATE DIRECT CHAT
    # =========================
    @app.route("/api/conversations/direct", methods=["POST"])
    @role_required(["employee", "manager", "admin", "super_admin"])
    def create_direct_conversation():
        other_user_id = request.json.get("user_id")
        user_id = session.get("user_id")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Check existing direct conversation
        c.execute("""
            SELECT c.id
            FROM conversations c
            JOIN conversation_participants p1 ON c.id = p1.conversation_id
            JOIN conversation_participants p2 ON c.id = p2.conversation_id
            WHERE c.is_group_chat = 0
              AND p1.user_id = ?
              AND p2.user_id = ?
        """, (user_id, other_user_id))

        row = c.fetchone()
        if row:
            conn.close()
            return jsonify({"conversation_id": row[0]}), 200

        # Create new conversation
        c.execute(
            "INSERT INTO conversations (is_group_chat, created_by_id) VALUES (0, ?)",
            (user_id,),
        )
        convo_id = c.lastrowid

        c.execute(
            "INSERT INTO conversation_participants (conversation_id, user_id) VALUES (?, ?)",
            (convo_id, user_id),
        )
        c.execute(
            "INSERT INTO conversation_participants (conversation_id, user_id) VALUES (?, ?)",
            (convo_id, other_user_id),
        )

        conn.commit()
        conn.close()

        return jsonify({"conversation_id": convo_id}), 201


    # =========================
    # GET MESSAGES
    # =========================
    @app.route("/api/conversations/<int:conversation_id>/messages", methods=["GET"])
    @role_required(["employee", "manager", "admin", "super_admin"])
    def get_messages(conversation_id):
        user_id = session.get("user_id")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            SELECT 1 FROM conversation_participants
            WHERE conversation_id = ? AND user_id = ?
        """, (conversation_id, user_id))

        if not c.fetchone():
            conn.close()
            return jsonify({"message": "Forbidden"}), 403

        c.execute("""
            SELECT m.id, m.content, m.created_at, u.email
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.conversation_id = ? AND m.is_deleted = 0
            ORDER BY m.created_at ASC
        """, (conversation_id,))

        rows = c.fetchall()
        conn.close()

        return jsonify([
            {
                "id": r[0],
                "content": r[1],
                "created_at": r[2],
                "sender_email": r[3]
            }
            for r in rows
        ]), 200


    # =========================
    # SEND MESSAGE
    # =========================
    @app.route("/api/conversations/<int:conversation_id>/messages", methods=["POST"])
    @role_required(["employee", "manager", "admin", "super_admin"])
    def send_message(conversation_id):
        content = request.json.get("content")
        user_id = session.get("user_id")

        if not content:
            return jsonify({"message": "Empty message"}), 400

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            SELECT 1 FROM conversation_participants
            WHERE conversation_id = ? AND user_id = ?
        """, (conversation_id, user_id))

        if not c.fetchone():
            conn.close()
            return jsonify({"message": "Forbidden"}), 403

        c.execute("""
            INSERT INTO messages (conversation_id, sender_id, content)
            VALUES (?, ?, ?)
        """, (conversation_id, user_id, content))

        message_id = c.lastrowid

        c.execute("SELECT created_at FROM messages WHERE id = ?", (message_id,))
        created_at = c.fetchone()[0]

        c.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        sender_email = c.fetchone()[0]

        conn.commit()
        conn.close()

        socketio.emit(
            "new_message",
            {
                "conversation_id": conversation_id,
                "message": {
                    "id": message_id,
                    "content": content,
                    "sender_email": sender_email,
                    "created_at": created_at,
                },
            },
            room=f"conversation_{conversation_id}",
        )

        return jsonify({"message_id": message_id}), 201


    # =========================
    # SOCKET EVENTS
    # =========================
    @socketio.on("join")
    def on_join(data):
        join_room(f"conversation_{data['conversation_id']}")

    @socketio.on("leave")
    def on_leave(data):
        leave_room(f"conversation_{data['conversation_id']}")

    @socketio.on("connect")
    def on_connect():
        if session.get("user_id"):
            emit(
                "user_status",
                {"user_id": session["user_id"], "status": "online"},
                broadcast=True,
            )

    @socketio.on("disconnect")
    def on_disconnect():
        if session.get("user_id"):
            emit(
                "user_status",
                {"user_id": session["user_id"], "status": "offline"},
                broadcast=True,
            )
