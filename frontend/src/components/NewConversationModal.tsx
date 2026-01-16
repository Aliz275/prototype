"use client";

import { useState } from "react";

export default function NewConversationModal({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState("");
  const [participants, setParticipants] = useState("");

  async function create() {
    await fetch("http://localhost:8000/api/conversations", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        participant_ids: participants.split(",").map(id => Number(id.trim())),
      }),
    });
    onClose();
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
      <div className="bg-white p-6 rounded w-96">
        <h2 className="font-bold mb-4">New Conversation</h2>

        <input
          className="border w-full p-2 mb-2"
          placeholder="Group name (optional)"
          value={name}
          onChange={e => setName(e.target.value)}
        />

        <input
          className="border w-full p-2 mb-4"
          placeholder="Participant IDs (comma separated)"
          value={participants}
          onChange={e => setParticipants(e.target.value)}
        />

        <div className="flex justify-end gap-2">
          <button onClick={onClose}>Cancel</button>
          <button onClick={create} className="bg-blue-600 text-white px-3 rounded">
            Create
          </button>
        </div>
      </div>
    </div>
  );
}
