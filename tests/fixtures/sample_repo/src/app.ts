import { Chatbot } from "chatbot-sdk";
import * as analytics from "analytics-lib";

export interface ConversationConfig {
  maxTokens: number;
  temperature: number;
}

export function startConversation(config: ConversationConfig): string {
  return "conversation-id";
}

export class ChatService {
  private config: ConversationConfig;

  constructor(config: ConversationConfig) {
    this.config = config;
  }

  sendMessage(text: string): void {
    console.log(text);
  }
}

async function loadHistory(userId: string): Promise<string[]> {
  return [];
}
