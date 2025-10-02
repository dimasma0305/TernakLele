import APIService from './services/api';

let cachedConfig: any = null;
let configPromise: Promise<any> | null = null;

export async function getServerConfig() {
  // Return cached config if available
  if (cachedConfig) {
    return cachedConfig;
  }

  // If a request is already in progress, wait for it
  if (configPromise) {
    return configPromise;
  }

  // Create new request
  configPromise = fetchConfig();
  cachedConfig = await configPromise;
  configPromise = null;

  return cachedConfig;
}

async function fetchConfig() {
  try {
    const { data } = await APIService.get('/get_config');
    return data;
  } catch (error) {
    console.error('Error fetching server config:', error);
    // Return default config if fetch fails
    return {
      FLAG_FORMAT: /FLG\{[A-Za-z0-9_]+\}/g
    };
  }
}

// Clear cache function for testing
export function clearConfigCache() {
  cachedConfig = null;
  configPromise = null;
}
