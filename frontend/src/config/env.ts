/** Centralized access to build-time environment variables. */
export const env = {
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, ''),
  appName: import.meta.env.VITE_APP_NAME ?? 'Genopedia',
} as const;
