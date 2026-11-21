import { api, jsonBody, refreshSession, setAccessToken } from './client';
import type {
  AIStatus,
  AnalysisDetail,
  AnalysisListItem,
  AuthResponse,
  ComparisonResult,
  User,
} from './types';

export async function signup(email: string, password: string, fullName?: string): Promise<AuthResponse> {
  const data = await api<AuthResponse>('/auth/signup', jsonBody({ email, password, full_name: fullName || undefined }), false);
  setAccessToken(data.access_token);
  return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const data = await api<AuthResponse>('/auth/login', jsonBody({ email, password }), false);
  setAccessToken(data.access_token);
  return data;
}

export async function logout(): Promise<void> {
  try {
    await api('/auth/logout', { method: 'POST' }, false);
  } finally {
    setAccessToken(null);
  }
}

export async function restoreSession(): Promise<User | null> {
  return refreshSession();
}

export async function me(): Promise<User> {
  return api<User>('/auth/me');
}

export interface AnalysisList {
  analyses: AnalysisListItem[];
  count: number;
}

export async function listAnalyses(): Promise<AnalysisList> {
  return api<AnalysisList>('/analyses');
}

export async function getAnalysis(id: number): Promise<AnalysisDetail> {
  return api<AnalysisDetail>(`/analyses/${id}`);
}

export async function createAnalysis(input: {
  name: string;
  content?: string;
  file?: File;
  format?: string;
  molecule?: string;
}): Promise<AnalysisDetail> {
  if (input.file) {
    const form = new FormData();
    form.append('file', input.file);
    form.append('name', input.name);
    if (input.format) form.append('format', input.format);
    if (input.molecule) form.append('molecule', input.molecule);
    return api<AnalysisDetail>('/analyses', { method: 'POST', body: form });
  }
  return api<AnalysisDetail>(
    '/analyses',
    jsonBody({ name: input.name, content: input.content, format: input.format ?? 'auto', molecule: input.molecule ?? 'DNA' }),
  );
}

export async function deleteAnalysis(id: number): Promise<void> {
  return api<void>(`/analyses/${id}`, { method: 'DELETE' });
}

export async function compareAnalyses(referenceId: number, sampleId: number): Promise<ComparisonResult> {
  return api<ComparisonResult>('/analyses/compare', jsonBody({ reference_id: referenceId, sample_id: sampleId }));
}

export async function fetchReportHtml(id: number): Promise<string> {
  return api<string>(`/analyses/${id}/report`, { headers: { Accept: 'text/html' } });
}

export async function aiStatus(): Promise<AIStatus> {
  return api<AIStatus>('/ai/status');
}
