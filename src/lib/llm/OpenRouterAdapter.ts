import OpenAI from 'openai'; // Using the OpenAI SDK as OpenRouter is compatible
import { ILLMAdapter, ChatRequest, ChatResponse, APIError, LLMTokens } from './ILLMAdapter';
import { LLM_ERRORS, getLLMError } from '../errors/llmErrors'; // Import catalog

const OPENROUTER_PRICING: Record<string, { prompt: number; completion: number; currency?: string }> = {
  'openai/gpt-3.5-turbo': { prompt: 0.0000005, completion: 0.0000015 },
  'openai/gpt-4': { prompt: 0.00003, completion: 0.00006 },
  'openai/gpt-4-turbo-preview': { prompt: 0.00001, completion: 0.00003 },
  'anthropic/claude-2': { prompt: 0.000008, completion: 0.000024 },
  'anthropic/claude-3-opus': { prompt: 0.000015, completion: 0.000075 },
  'anthropic/claude-3-sonnet': { prompt: 0.000003, completion: 0.000015 },
  'google/gemini-pro': { prompt: 0.000000125, completion: 0.000000375 },
  'mistralai/mistral-7b': { prompt: 0.00000025, completion: 0.00000025 },
  'mistralai/mixtral-8x7b': { prompt: 0.0000007, completion: 0.0000007 },
  'openrouter/auto': { prompt: 0.000001, completion: 0.000002 },
  'default': { prompt: 0.000001, completion: 0.000002 },
};

function calculateOpenRouterCost(model: string, tokens: LLMTokens | undefined): number | undefined {
  if (!tokens || tokens.prompt_tokens === undefined || tokens.completion_tokens === undefined) {
    return undefined;
  }
  let pricingKey = model;
  if (!OPENROUTER_PRICING[pricingKey] && pricingKey.includes(':')) {
    pricingKey = pricingKey.substring(0, pricingKey.indexOf(':'));
  }
  const pricing = OPENROUTER_PRICING[pricingKey] || OPENROUTER_PRICING[model] || OPENROUTER_PRICING['default'];
  const cost = (tokens.prompt_tokens * pricing.prompt) + (tokens.completion_tokens * pricing.completion);
  return parseFloat(cost.toFixed(10));
}

export class OpenRouterAdapter implements ILLMAdapter {
  private client: OpenAI;

  constructor() {
    const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY || "sk-or-your-openrouter-api-key";
    const HTTP_REFERER = process.env.HTTP_REFERER || "https://kutsaka.ai";
    const X_TITLE = process.env.X_TITLE || "Kutsaka AI";

    if (!OPENROUTER_API_KEY || OPENROUTER_API_KEY === "sk-or-your-openrouter-api-key") {
      console.warn("OpenRouterAdapter: OPENROUTER_API_KEY is not set or is using a placeholder.");
    }

    this.client = new OpenAI({
      baseURL: "https://openrouter.ai/api/v1",
      apiKey: OPENROUTER_API_KEY,
      defaultHeaders: {
        "HTTP-Referer": HTTP_REFERER,
        "X-Title": X_TITLE,
      },
    });
  }

  async chatCompletion(request: ChatRequest): Promise<ChatResponse> {
    console.log('OpenRouterAdapter: chatCompletion called with:', request);
    try {
      const requestedModel = request.model || 'openrouter/auto';

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

      const cost = calculateOpenRouterCost(completion.model, responseTokens);

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
    console.error('OpenRouterAdapter: handleError called with:', error);
    if (error instanceof OpenAI.APIError) { // OpenRouter uses OpenAI-compatible error structures
      switch (error.status) {
        case 401: // Unauthorized
          return { ...getLLMError('AUTHENTICATION_ERROR'), details: error.message, type: error.type, param: error.param };
        case 429: // Rate limit
          return { ...getLLMError('RATE_LIMIT'), details: error.message, type: error.type, param: error.param };
        case 403: // Forbidden - often quota issues or access permissions on OpenRouter
           if (error.message && error.message.toLowerCase().includes('quota')) {
             return { ...getLLMError('PROVIDER_ERROR'), response: "Quota exceeded. Please check your OpenRouter account.", details: error.message, type: error.type, param: error.param };
           }
           // Could be a more general permission issue not necessarily auth key related
           return { ...getLLMError('PROVIDER_ERROR'), response: "Access forbidden by OpenRouter.", details: error.message, type: error.type, param: error.param };
        case 400: // Bad Request - could be various issues
           if (error.message && error.message.toLowerCase().includes('moderation')) {
             return { ...getLLMError('CONTENT_MODERATION'), details: error.message, type: error.type, param: error.param };
           }
           // For other 400 errors on OpenRouter
           return {
             code: error.status,
             message: `OpenRouter Bad Request: ${error.message}`,
             type: error.type,
             param: error.param,
             details: error.error?.toString() || "Invalid request to OpenRouter."
           };
        // Check for 451 if OpenRouter uses it for content moderation as per earlier thoughts
        // case 451:
        //   return { ...getLLMError('CONTENT_MODERATION'), details: error.message, type: error.type, param: error.param };
        default:
          // For other OpenRouter API errors
          return {
            ...getLLMError('PROVIDER_ERROR'),
            code: error.status || 500,
            message: error.message,
            type: error.type,
            param: error.param,
            details: `Unhandled OpenRouter API error. Status: ${error.status}`
          };
      }
    } else if (error instanceof Error) {
      return { ...getLLMError('INTERNAL_SERVER_ERROR'), details: error.message, message: error.message };
    }
    return { ...getLLMError('INTERNAL_SERVER_ERROR'), details: 'An unknown error occurred in OpenRouterAdapter' };
  }
}
