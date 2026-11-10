// Production build. Values come from env.js, which the release pipeline writes for
// each environment (test, prod), so one build artifact can be deployed everywhere.
interface RuntimeEnv {
  apiUrl?: string;
  azureMapsKey?: string;
}

const runtime: RuntimeEnv = (globalThis as { __env?: RuntimeEnv }).__env ?? {};

export const environment = {
  production: true,
  apiUrl: runtime.apiUrl || '/api',
  azureMapsKey: runtime.azureMapsKey || '',
};