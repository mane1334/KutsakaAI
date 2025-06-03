import { z } from 'zod';

// Define a schema for a single message
const MessageSchema = z.object({
  role: z.enum(['user', 'assistant', 'system']), // Adjust roles as per your application's needs
  content: z.string().min(1, "Message content cannot be empty."),
  // Add any other fields a message might have, e.g., name, tool_calls
});

// Define the main request schema
export const ChatRequestSchema = z.object({
  messages: z.array(MessageSchema)
    .min(1, "At least one message is required.")
    .max(20, "Number of messages cannot exceed 20."),
  model: z.string().optional(), // Or a more specific enum if you have a fixed set of models
  max_tokens: z.number()
    .int("Max tokens must be an integer.")
    .positive("Max tokens must be a positive number.")
    .max(1500, "Max tokens cannot exceed 1500.")
    .default(500),
  temperature: z.number().min(0).max(2).optional(), // Common range for temperature
  top_p: z.number().min(0).max(1).optional(), // Common range for top_p
  stream: z.boolean().optional(),
  // Add any other parameters you expect in the chat request
  // Example: user: z.string().optional(),
});

// Example of how to use the schema:
/*
export function validateChatRequest(data: unknown) {
  try {
    const validatedData = ChatRequestSchema.parse(data);
    return { isValid: true, data: validatedData, errors: null };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { isValid: false, data: null, errors: error.flatten() };
    }
    // Handle unexpected errors
    throw error;
  }
}

// Sample Usage:
const requestData = {
  messages: [
    { role: 'user', content: 'Hello there!' },
    { role: 'assistant', content: 'Hi!' }
  ],
  max_tokens: 100
};

const validationResult = validateChatRequest(requestData);
if (validationResult.isValid) {
  console.log("Request is valid:", validationResult.data);
} else {
  console.error("Validation errors:", validationResult.errors);
}
*/
