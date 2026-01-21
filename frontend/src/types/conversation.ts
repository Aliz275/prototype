//frontend/src/types/conversation.ts

export type Participant = {
    id: number;
    email: string;
  };
  
  export type Conversation = {
    id: number;
    name: string | null;
    is_group_chat: boolean;
    participants: Participant[];
  };