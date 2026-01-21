//frontend/src/components/CreateGroupModal.tsx


"use client";

import { useEffect, useState } from "react";

type User = {
  id: number;
  email: string;
};

export default function CreateGroupModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [users, setUsers] = useState<User[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [name, setName] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/api/users", {
      credentials: "include",
    })
      .then(res => res.json())
      .then(setUsers);
  }, []);

  function toggle(id: number) {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  }

  async function createGroup() {
    if (!name || selected.length === 0) return;

    await fetch("http://localhost:8000/api/conversations/group", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        participants: selected,
      }),
    });

    onCreated();
    onClose();
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
      <div className="bg-white w-96 rounded-lg p-4">
        <h2 className="font-bold text-lg mb-3">New Group</h2>

        <input
          placeholder="Group name"
          className="border w-full mb-3 px-2 py-1"
          value={name}
          onChange={e => setName(e.target.value)}
        />

        <div className="max-h-48 overflow-y-auto border p-2 mb-3">
          {users.map(u => (
            <label key={u.id} className="block">
              <input
                type="checkbox"
                checked={selected.includes(u.id)}
                onChange={() => toggle(u.id)}
              />{" "}
              {u.email}
            </label>
          ))}
        </div>

        <div className="flex justify-end gap-2">
          <button onClick={onClose}>Cancel</button>
          <button
            className="bg-green-600 text-white px-3 py-1 rounded"
            onClick={createGroup}
          >
            Create
          </button>
        </div>
      </div>
    </div>
  );
}
