import { ILLMAdapter } from './ILLMAdapter';
import { OpenAIAdapter } from './OpenAIAdapter';
import { OpenRouterAdapter } from './OpenRouterAdapter';

// Assume environment variables are handled elsewhere and accessible, e.g., via a config service or process.env
// For example, you might have something like:
// import { env } from '@/config/env'; // Adjust path as per your project structure

export type AIProviderType = 'openai' | 'openrouter';

export class AdapterFactory {
  public static createAdapter(provider: AIProviderType): ILLMAdapter {
    // Read provider from environment variables, defaulting to 'openai' if not set.
    // const currentProvider = env.AI_PROVIDER || 'openai'; // Example of env var usage

    // For this factory, we will use the 'provider' argument directly.
    // In a real application, you might prefer to rely on an environment variable.

    if (provider === 'openai') {
      return new OpenAIAdapter();
    } else if (provider === 'openrouter') {
      return new OpenRouterAdapter();
    } else {
      // Fallback or default provider
      console.warn(`Unsupported AI provider: ${provider}. Defaulting to OpenAI.`);
      return new OpenAIAdapter(); // Or throw an error
    }
  }
}

// Example Usage (optional, can be removed or kept for testing):
/*
(async () => {
  // Example: Get provider from an environment variable or configuration
  const providerType = process.env.AI_PROVIDER as AIProviderType || 'openai';

  const adapter = AdapterFactory.createAdapter(providerType);

  try {
    const response = await adapter.chatCompletion({
      messages: [{ role: 'user', content: 'Hello, LLM!' }],
      // ... other request parameters
    });
    console.log('Chat Completion Response:', response);
  } catch (error) {
    const apiError = adapter.handleError(error);
    console.error('API Error:', apiError);
  }
})();
*/
