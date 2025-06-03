import OpenAI from 'openai';
import { ILLMAdapter, ChatRequest, ChatResponse, APIError, LLMTokens } from './ILLMAdapter';
// import { ChatRequestSchema } from '../validation/requestSchema'; // For validating request (optional here)

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

  // Normalize model name: sometimes models are returned with version/date suffixes by the API
  let baseModel = model.toLowerCase();
  if (baseModel.startsWith('gpt-3.5-turbo-')) baseModel = 'gpt-3.5-turbo';
  if (baseModel.startsWith('gpt-4-') && baseModel.includes('-preview')) baseModel = 'gpt-4-turbo-preview'; // Or a more general gpt-4 mapping
  else if (baseModel.startsWith('gpt-4-')) baseModel = 'gpt-4';


  const pricing = OPENAI_PRICING[baseModel] || OPENAI_PRICING['default'];
  const cost = (tokens.prompt_tokens * pricing.prompt) + (tokens.completion_tokens * pricing.completion);
  return parseFloat(cost.toFixed(6)); // Return cost with a fixed number of decimal places
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
      // Use the model from the request, or default if not provided.
      // The actual model used by OpenAI API will be in `completion.model`
      const requestedModel = request.model || 'gpt-3.5-turbo';

      const completion = await this.client.chat.completions.create({
        model: requestedModel,
        messages: request.messages as any, // Cast if necessary
        max_tokens: request.max_tokens,
        temperature: request.temperature,
        top_p: request.top_p,
        stream: request.stream,
        // extra_body: { /* ... */ }
      });

      const responseTokens: LLMTokens | undefined = completion.usage ? {
        prompt_tokens: completion.usage.prompt_tokens,
        completion_tokens: completion.usage.completion_tokens,
        total_tokens: completion.usage.total_tokens,
      } : undefined;

      // Use the model string returned by OpenAI in `completion.model` for cost calculation,
      // as it's the ground truth of what was actually used.
      const cost = calculateCost(completion.model, responseTokens);

      return {
        id: completion.id,
        object: completion.object,
        created: completion.created,
        model: completion.model, // This is the model string returned by OpenAI
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
      return {
        code: error.status || 500,
        message: error.message,
        type: error.type,
        param: error.param,
      };
    } else if (error instanceof Error) {
      return { code: 500, message: error.message };
    }
    return { code: 500, message: 'An unknown error occurred in OpenAIAdapter' };
  }
}
