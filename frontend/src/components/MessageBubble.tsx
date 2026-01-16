export default function MessageBubble({ message }: any) {
    return (
      <div className="mb-2">
        <div className="text-xs text-gray-500">{message.sender_email}</div>
        <div className="inline-block bg-white p-2 rounded shadow">
          {message.content}
        </div>
      </div>
    );
  }
  