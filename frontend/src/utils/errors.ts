interface ApiErrorResponse {
  detail?: unknown;
}

interface WithResponse {
  response?: {
    data?: ApiErrorResponse;
  };
  message?: string;
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null;

export const getApiErrorMessage = (error: unknown, fallback = 'Something went wrong. Please try again.') => {
  if (isRecord(error) && 'response' in error) {
    const response = (error as WithResponse).response;
    const detail = response?.data?.detail;

    if (Array.isArray(detail)) {
      return detail
        .map((entry) => {
          if (isRecord(entry)) {
            const field = Array.isArray(entry.loc) ? entry.loc.join('.') : 'field';
            return `${field}: ${entry.msg ?? 'Invalid value'}`;
          }
          return String(entry);
        })
        .join('; ');
    }

    if (typeof detail === 'string') {
      return detail;
    }

    if (isRecord(detail)) {
      return JSON.stringify(detail);
    }
  }

  if (isRecord(error) && typeof (error as WithResponse).message === 'string') {
    return (error as WithResponse).message as string;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
};


