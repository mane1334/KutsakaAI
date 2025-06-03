export interface ChatRequest {
  // Define the structure of ChatRequest based on your project's needs
  messages: any[]; // Replace 'any' with a more specific type if possible
  model?: string; // Added model as it's common
  max_tokens?: number; // Added max_tokens
  temperature?: number; // Added temperature
  top_p?: number; // Added top_p
  stream?: boolean; // Added stream
  [key: string]: any; // Allow other properties
}

export interface LLMTokens {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ChatResponse {
  id: string; // Example: 'chatcmpl-xxxx'
  object: string; // Example: 'chat.completion'
  created: number; // Timestamp
  model: string; // Model used
  choices: Array<{
    index: number;
    message: {
      role: string; // 'assistant', 'user', etc.
      content: string | null;
      // Potentially tool_calls, etc.
    };
    finish_reason: string; // 'stop', 'length', etc.
  }>;
  usage?: LLMTokens; // Making usage itself optional as before, but now typed
  cost?: number; // Calculated cost for the request (optional)
  // Allow other properties as before
  [key: string]: any;
}

export interface APIError {
  // Define the structure of APIError based on your project's needs
  code: number;
  message: string;
  type?: string; // Added from OpenAI error
  param?: string | null; // Added from OpenAI error
  [key: string]: any; // Allow other properties
}

export interface ILLMAdapter {
  chatCompletion(request: ChatRequest): Promise<ChatResponse>;
  handleError(error: unknown): APIError;
}
