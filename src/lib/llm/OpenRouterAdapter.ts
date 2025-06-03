import OpenAI from 'openai'; // Using the OpenAI SDK as OpenRouter is compatible
import { ILLMAdapter, ChatRequest, ChatResponse, APIError, LLMTokens } from './ILLMAdapter';
// import { ChatRequestSchema } from '../validation/requestSchema'; // For validating request (optional here)

// Placeholder for OpenRouter pricing.
// Keys should ideally match the model strings returned by OpenRouter (e.g., "openai/gpt-3.5-turbo").
// Prices are per token. Note: OpenRouter's actual pricing can be complex and dynamic.
// These are simplified examples and might need adjustment based on real-time data or a dedicated pricing service.
const OPENROUTER_PRICING: Record<string, { prompt: number; completion: number; currency?: string }> = {
  'openai/gpt-3.5-turbo': { prompt: 0.0000005, completion: 0.0000015 }, // Example: $0.0005/1K prompt, $0.0015/1K completion
  'openai/gpt-4': { prompt: 0.00003, completion: 0.00006 },         // Example: $0.03/1K prompt, $0.06/1K completion
  'openai/gpt-4-turbo-preview': { prompt: 0.00001, completion: 0.00003 }, // Example: $0.01/1K prompt, $0.03/1K completion
  'anthropic/claude-2': { prompt: 0.000008, completion: 0.000024 },   // Example: $0.008/1K prompt, $0.024/1K completion
  'anthropic/claude-3-opus': { prompt: 0.000015, completion: 0.000075 }, // Example: $0.015/1K prompt, $0.075/1K completion
  'anthropic/claude-3-sonnet': { prompt: 0.000003, completion: 0.000015 }, // Example: $0.003/1K prompt, $0.015/1K completion
  'google/gemini-pro': { prompt: 0.000000125, completion: 0.000000375 }, // Example pricing for Gemini Pro
  'mistralai/mistral-7b': { prompt: 0.00000025, completion: 0.00000025 }, // Example
  'mistralai/mixtral-8x7b': { prompt: 0.0000007, completion: 0.0000007 }, // Example
  'openrouter/auto': { prompt: 0.000001, completion: 0.000002 }, // A generic fallback if model is 'auto' or for unknown routed models
  'default': { prompt: 0.000001, completion: 0.000002 }, // Default fallback for unknown models
};

// Helper function to calculate cost for OpenRouter models
function calculateOpenRouterCost(model: string, tokens: LLMTokens | undefined): number | undefined {
  if (!tokens || tokens.prompt_tokens === undefined || tokens.completion_tokens === undefined) {
    return undefined;
  }

  // OpenRouter model names are usually like "vendor/model-name" or "vendor/model-name:version"
  // We use the model string directly as returned by the API for lookup.
  // If it contains a version (e.g., :xxxx), try stripping it for a more general match if the specific version isn't found.
  let pricingKey = model;
  if (!OPENROUTER_PRICING[pricingKey] && pricingKey.includes(':')) {
    pricingKey = pricingKey.substring(0, pricingKey.indexOf(':'));
  }

  const pricing = OPENROUTER_PRICING[pricingKey] || OPENROUTER_PRICING[model] || OPENROUTER_PRICING['default'];

  const cost = (tokens.prompt_tokens * pricing.prompt) + (tokens.completion_tokens * pricing.completion);
  // OpenRouter costs can be very small and might require more precision.
  // Their dashboard often shows costs up to 10 decimal places.
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
      // Determine the model to request. OpenRouter uses 'vendor/model' slugs or 'openrouter/auto'.
      const requestedModel = request.model || 'openrouter/auto';

      const completion = await this.client.chat.completions.create({
        model: requestedModel,
        messages: request.messages as any,
        max_tokens: request.max_tokens,
        temperature: request.temperature,
        top_p: request.top_p,
        stream: request.stream,
        // extra_body: { /* for transforms like moderation if applicable */ }
      });

      const responseTokens: LLMTokens | undefined = completion.usage ? {
        prompt_tokens: completion.usage.prompt_tokens,
        completion_tokens: completion.usage.completion_tokens,
        total_tokens: completion.usage.total_tokens,
      } : undefined;

      // Use the model string returned by OpenRouter in completion.model for cost calculation
      const cost = calculateOpenRouterCost(completion.model, responseTokens);

      return {
        id: completion.id,
        object: completion.object,
        created: completion.created,
        model: completion.model, // This is the actual model string from OpenRouter's response
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
    if (error instanceof OpenAI.APIError) {
      return {
        code: error.status || 500,
        message: error.message,
        type: error.type,
        param: error.param,
      };
    } else if (error instanceof Error) {
      return { code: 500, message: error.message };
    }
    return { code: 500, message: 'An unknown error occurred in OpenRouterAdapter' };
  }
}
