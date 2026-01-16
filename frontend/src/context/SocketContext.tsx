"use client";

import React, { createContext, useContext, useEffect } from "react";
import type { Socket } from "socket.io-client";
import { socket } from "../lib/socket";

const SocketContext = createContext<Socket | null>(null);

export function SocketProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Connect once when provider mounts
    socket.connect();

    // Cleanup MUST return void
    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <SocketContext.Provider value={socket}>
      {children}
    </SocketContext.Provider>
  );
}

export function useSocket() {
  const context = useContext(SocketContext);

  if (!context) {
    throw new Error("useSocket must be used within a SocketProvider");
  }

  return context;
}
