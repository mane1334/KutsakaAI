export interface LLMError {
  code: number;
  response: string;
  description?: string; // Optional field for more detailed internal description
}

export interface LLMErrorCatalog {
  [key: string]: LLMError;
}

export const LLM_ERRORS: LLMErrorCatalog = {
  RATE_LIMIT: {
    code: 429,
    response: "Serviço sobrecarregado. Tente em 1 minuto",
    description: "Error due to too many requests hitting the API rate limits."
  },
  CONTENT_MODERATION: {
    code: 451, // Using 451 as 'Unavailable For Legal Reasons' can fit content policy
    response: "Conteúdo bloqueado por políticas de segurança",
    description: "Error due to content violating security or moderation policies."
  },
  // Example of another common error type:
  AUTHENTICATION_ERROR: {
    code: 401,
    response: "Erro de autenticação. Verifique suas credenciais.",
    description: "Error due to invalid or missing API key or authentication token."
  },
  PROVIDER_ERROR: {
    code: 502, // Bad Gateway, can indicate an issue with the upstream LLM provider
    response: "O provedor de LLM está com problemas. Tente mais tarde.",
    description: "Error originating from the LLM provider's side."
  },
  INTERNAL_SERVER_ERROR: {
    code: 500,
    response: "Ocorreu um erro interno no servidor.",
    description: "A generic internal server error."
  }
};

// Function to get an error by its key, useful for type safety
export function getLLMError(key: keyof typeof LLM_ERRORS): LLMError {
  return LLM_ERRORS[key];
}
