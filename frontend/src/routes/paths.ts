export const paths = {
  landing: '/',
  login: '/login',
  register: '/register',
  dashboard: '/app',
  analyze: '/app/analyze',
  analysis: (id: number | string) => `/app/analyses/${id}`,
  compare: '/app/compare',
  ai: '/app/ai',
  settings: '/app/settings',
} as const;
