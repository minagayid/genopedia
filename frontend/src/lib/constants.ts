/** React Query cache keys — keep all keys here to avoid typos and collisions. */
export const QUERY_KEYS = {
  health: ['health'],
  doctorDashboard: ['doctor', 'dashboard'],
  records: ['records'],
  record: (id: number) => ['records', id],
  prescriptions: ['prescriptions'],
  prescription: (id: number) => ['prescriptions', id],
  pharmacies: ['pharmacies'],
  pharmacySearch: (lat: number, lon: number, radius: number) =>
    ['pharmacies', 'search', lat, lon, radius],
  adherence: (patientId: number) => ['adherence', patientId],
  adherenceScore: (patientId: number) => ['adherence', patientId, 'score'],
  appointments: ['appointments'],
  appointment: (id: number) => ['appointments', id],
  aiResult: (analysisId: string) => ['ai', 'results', analysisId],
} as const;

export const STORAGE_KEYS = {
  auth: 'homzdoctor-auth',
} as const;

export const USER_ROLES = ['patient', 'doctor', 'admin'] as const;
