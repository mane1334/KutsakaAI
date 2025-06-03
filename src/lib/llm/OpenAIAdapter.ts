import OpenAI from 'openai';
import { ILLMAdapter, ChatRequest, ChatResponse, APIError, LLMTokens } from './ILLMAdapter';
import { LLM_ERRORS, getLLMError } from '../errors/llmErrors'; // Import catalog

// Placeholder for a more sophisticated pricing model/service
const OPENAI_PRICING: Record<string, { prompt: number; completion: number }> = {
  'gpt-3.5-turbo': { prompt: 0.0005 / 1000, completion: 0.0015 / 1000 }, // Example: $0.0005/1K prompt, $0.0015/1K completion
  'gpt-4': { prompt: 0.03 / 1000, completion: 0.06 / 1000 }, // Example: $0.03/1K prompt, $0.06/1K completion
  'gpt-4-turbo-preview': { prompt: 0.01 / 1000, completion: 0.03 / 1000 }, // Example pricing
  'gpt-4-1106-preview': { prompt: 0.01 / 1000, completion: 0.03 / 1000 }, // Example pricing
  'default': { prompt: 0.001 / 1000, completion: 0.002 / 1000 }, // Default fallback
};

function calculateCost(model: string, tokens: LLMTokens | undefined): number | undefined {
  if (!tokens || tokens.prompt_tokens === undefined || tokens.completion_tokens === undefined) {
    return undefined;
  }

  let baseModel = model.toLowerCase();
  if (baseModel.startsWith('gpt-3.5-turbo-')) baseModel = 'gpt-3.5-turbo';
  if (baseModel.startsWith('gpt-4-') && baseModel.includes('-preview')) baseModel = 'gpt-4-turbo-preview';
  else if (baseModel.startsWith('gpt-4-')) baseModel = 'gpt-4';

  const pricing = OPENAI_PRICING[baseModel] || OPENAI_PRICING['default'];
  const cost = (tokens.prompt_tokens * pricing.prompt) + (tokens.completion_tokens * pricing.completion);
  return parseFloat(cost.toFixed(6));
}

export class OpenAIAdapter implements ILLMAdapter {
  private client: OpenAI;

  constructor() {
    const OPENAI_API_KEY = process.env.OPENAI_API_KEY || "sk-your-openai-api-key";
    if (!OPENAI_API_KEY || OPENAI_API_KEY === "sk-your-openai-api-key") {
      console.warn("OpenAIAdapter: OPENAI_API_KEY is not set or is using a placeholder. Please configure it.");
    }
    this.client = new OpenAI({
      apiKey: OPENAI_API_KEY,
    });
  }

  async chatCompletion(request: ChatRequest): Promise<ChatResponse> {
    console.log('OpenAIAdapter: chatCompletion called with:', request);
    try {
      const requestedModel = request.model || 'gpt-3.5-turbo';

      const completion = await this.client.chat.completions.create({
        model: requestedModel,
        messages: request.messages as any,
        max_tokens: request.max_tokens,
        temperature: request.temperature,
        top_p: request.top_p,
        stream: request.stream,
      });

      const responseTokens: LLMTokens | undefined = completion.usage ? {
        prompt_tokens: completion.usage.prompt_tokens,
        completion_tokens: completion.usage.completion_tokens,
        total_tokens: completion.usage.total_tokens,
      } : undefined;

      const cost = calculateCost(completion.model, responseTokens);

      return {
        id: completion.id,
        object: completion.object,
        created: completion.created,
        model: completion.model,
        choices: completion.choices.map(choice => ({
          index: choice.index,
          message: {
            role: choice.message.role,
            content: choice.message.content,
          },
          finish_reason: choice.finish_reason,
        })),
        usage: responseTokens,
        cost: cost,
      };
    } catch (error) {
      throw error;
    }
  }

  handleError(error: unknown): APIError {
    console.error('OpenAIAdapter: handleError called with:', error);
    if (error instanceof OpenAI.APIError) {
      switch (error.status) {
        case 401: // Unauthorized
          return { ...getLLMError('AUTHENTICATION_ERROR'), details: error.message, type: error.type, param: error.param };
        case 429: // Rate limit or engine overload
          return { ...getLLMError('RATE_LIMIT'), details: error.message, type: error.type, param: error.param };
        case 400: // Bad Request
          // OpenAI uses error.code 'billing_hard_limit_reached' for quota issues under a 400 status for some APIs,
          // or error.type 'invalid_request_error' for moderation issues.
          if (error.code === 'billing_hard_limit_reached') {
             return { ...getLLMError('PROVIDER_ERROR'), response: "OpenAI quota exceeded.", details: error.message, type: error.type, param: error.param };
          }
          if (error.message && error.message.toLowerCase().includes('moderation')) { // Check message for moderation
             return { ...getLLMError('CONTENT_MODERATION'), details: error.message, type: error.type, param: error.param };
          }
          // For other 400 errors, return more generic info or specific if identifiable
          return {
            code: error.status,
            message: `OpenAI Bad Request: ${error.message}`,
            type: error.type,
            param: error.param,
            details: error.error?.toString() || "Invalid request structure or parameters."
          };
        default:
          // For other OpenAI API errors, use PROVIDER_ERROR or a more generic one
          return {
            ...getLLMError('PROVIDER_ERROR'), // Default to provider error for unhandled API errors
            code: error.status || 500, // Ensure code from error is used if available
            message: error.message, // Original message from OpenAI
            type: error.type,
            param: error.param,
            details: `Unhandled OpenAI API error. Status: ${error.status}`
          };
      }
    } else if (error instanceof Error) {
      // Generic JavaScript error
      return { ...getLLMError('INTERNAL_SERVER_ERROR'), details: error.message, message: error.message };
    }
    // Fallback for unknown errors
    return { ...getLLMError('INTERNAL_SERVER_ERROR'), details: 'An unknown error occurred in OpenAIAdapter' };
  }
}
