from flask import request, jsonify, session
from flask_socketio import emit, join_room, leave_room
from app.auth import role_required
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database.db")


def init_messaging_routes(app, socketio):

    # =========================
    # CREATE CONVERSATION (DIRECT OR GROUP)
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

        if is_group_chat and role not in ["manager", "admin", "super_admin"]:
            return jsonify({"message": "Permission denied"}), 403

        name = data.get("name") if is_group_chat else None

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            """
            INSERT INTO conversations (name, is_group_chat, created_by_id)
            VALUES (?, ?, ?)
            """,
            (name, int(is_group_chat), user_id),
        )
        conversation_id = c.lastrowid

        for pid in participant_ids:
            c.execute(
                """
                INSERT INTO conversation_participants (conversation_id, user_id)
                VALUES (?, ?)
                """,
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
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute(
            """
            SELECT DISTINCT c.id, c.name, c.is_group_chat, um.unread_count
            FROM conversations c
            JOIN conversation_participants cp ON cp.conversation_id = c.id
            LEFT JOIN unread_messages um
              ON um.conversation_id = c.id AND um.user_id = ?
            WHERE cp.user_id = ?
            ORDER BY c.last_message_at DESC
            """,
            (user_id, user_id),
        )

        conversations = []

        for row in c.fetchall():
            c.execute(
                """
                SELECT u.id, u.email
                FROM users u
                JOIN conversation_participants cp
                  ON u.id = cp.user_id
                WHERE cp.conversation_id = ?
                """,
                (row["id"],),
            )

            participants = [
                {"id": p["id"], "email": p["email"]}
                for p in c.fetchall()
            ]

            name = row["name"]
            if not row["is_group_chat"]:
                for p in participants:
                    if p["id"] != user_id:
                        name = p["email"]
                        break

            conversations.append(
                {
                    "id": row["id"],
                    "name": name,
                    "is_group_chat": bool(row["is_group_chat"]),
                    "participants": participants,
                    "unread_count": row["unread_count"] or 0,
                }
            )

        conn.close()
        return jsonify(conversations), 200

    # =========================
    # GET CONVERSATION PARTICIPANTS (GROUP DETAILS)
    # =========================
    @app.route("/api/conversations/<int:conversation_id>/participants", methods=["GET"])
    @role_required(["employee", "manager", "admin", "super_admin"])
    def get_participants(conversation_id):
        user_id = session.get("user_id")

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Ensure requester is in conversation
        c.execute(
            """
            SELECT 1 FROM conversation_participants
            WHERE conversation_id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        )

        if not c.fetchone():
            conn.close()
            return jsonify({"message": "Forbidden"}), 403

        c.execute(
            """
            SELECT u.id, u.email, u.role
            FROM users u
            JOIN conversation_participants cp ON cp.user_id = u.id
            WHERE cp.conversation_id = ?
            """,
            (conversation_id,),
        )

        participants = [
            {"id": row["id"], "email": row["email"], "role": row["role"]}
            for row in c.fetchall()
        ]

        conn.close()
        return jsonify(participants), 200

    # =========================
    # REMOVE PARTICIPANT (SUPER ADMIN)
    # =========================
    @app.route(
        "/api/conversations/<int:conversation_id>/participants/<int:user_id>",
        methods=["DELETE"],
    )
    @role_required(["super_admin"])
    def remove_participant(conversation_id, user_id):
        requester_id = session.get("user_id")

        if requester_id == user_id:
            return jsonify({"message": "Cannot remove yourself"}), 400

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            """
            SELECT 1 FROM conversation_participants
            WHERE conversation_id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        )

        if not c.fetchone():
            conn.close()
            return jsonify({"message": "User not in conversation"}), 404

        c.execute(
            """
            DELETE FROM conversation_participants
            WHERE conversation_id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        )

        conn.commit()
        conn.close()

        return jsonify({"success": True}), 200

    # =========================
    # DIRECT CHAT (SAFE)
    # =========================
    @app.route("/api/conversations/direct", methods=["POST"])
    @role_required(["employee", "manager", "admin", "super_admin"])
    def create_direct_conversation():
        other_user_id = request.json.get("user_id")
        user_id = session.get("user_id")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            """
            SELECT c.id
            FROM conversations c
            JOIN conversation_participants a ON c.id = a.conversation_id
            JOIN conversation_participants b ON c.id = b.conversation_id
            WHERE c.is_group_chat = 0
              AND a.user_id = ?
              AND b.user_id = ?
            """,
            (user_id, other_user_id),
        )

        existing = c.fetchone()
        if existing:
            conn.close()
            return jsonify({"conversation_id": existing[0]}), 200

        c.execute(
            """
            INSERT INTO conversations (is_group_chat, created_by_id)
            VALUES (0, ?)
            """,
            (user_id,),
        )
        convo_id = c.lastrowid

        c.executemany(
            """
            INSERT INTO conversation_participants (conversation_id, user_id)
            VALUES (?, ?)
            """,
            [(convo_id, user_id), (convo_id, other_user_id)],
        )

        conn.commit()
        conn.close()

        return jsonify({"conversation_id": convo_id}), 201

    # =========================
    # DELETE CONVERSATION (SUPER ADMIN)
    # =========================
    @app.route("/api/conversations/<int:conversation_id>", methods=["DELETE"])
    @role_required(["super_admin"])
    def delete_conversation(conversation_id):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        c.execute("DELETE FROM conversation_participants WHERE conversation_id = ?", (conversation_id,))
        c.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))

        conn.commit()
        conn.close()

        return jsonify({"message": "Conversation deleted"}), 200

    # =========================
    # MESSAGES
    # =========================
    @app.route("/api/conversations/<int:conversation_id>/messages", methods=["GET"])
    @role_required(["employee", "manager", "admin", "super_admin"])
    def get_messages(conversation_id):
        user_id = session.get("user_id")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            """
            SELECT 1 FROM conversation_participants
            WHERE conversation_id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        )

        if not c.fetchone():
            conn.close()
            return jsonify({"message": "Forbidden"}), 403

        c.execute(
            """
            SELECT m.id, m.content, m.created_at, u.email, m.status
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.conversation_id = ?
            ORDER BY m.created_at ASC
            """,
            (conversation_id,),
        )

        messages = []
        for row in c.fetchall():
            messages.append(
                {
                    "id": row[0],
                    "content": row[1],
                    "created_at": row[2],
                    "sender_email": row[3],
                    "status": row[4],
                }
            )

        conn.close()
        return jsonify(messages), 200

    @app.route("/api/conversations/<int:conversation_id>/messages", methods=["POST"])
    @role_required(["employee", "manager", "admin", "super_admin"])
    def send_message(conversation_id):
        content = request.json.get("content")
        user_id = session.get("user_id")

        if not content:
            return jsonify({"message": "Empty message"}), 400

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            "INSERT INTO messages (conversation_id, sender_id, content) VALUES (?, ?, ?)",
            (conversation_id, user_id, content),
        )
        msg_id = c.lastrowid

        c.execute(
            "UPDATE conversations SET last_message_at = ? WHERE id = ?",
            (datetime.utcnow(), conversation_id),
        )

        c.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        email = c.fetchone()[0]

        conn.commit()
        conn.close()

        socketio.emit(
            "new_message",
            {
                "conversation_id": conversation_id,
                "message": {
                    "id": msg_id,
                    "content": content,
                    "sender_email": email,
                },
            },
            room=f"conversation_{conversation_id}",
        )

        return jsonify({"message_id": msg_id}), 201

    # =========================
    # SOCKET EVENTS
    # =========================
    @socketio.on("join")
    def on_join(data):
        join_room(f"conversation_{data['conversation_id']}")

    @socketio.on("leave")
    def on_leave(data):
        leave_room(f"conversation_{data['conversation_id']}")
