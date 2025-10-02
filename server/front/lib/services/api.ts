// Get API URL based on environment
const getApiUrl = (): string => {
  if (typeof window === 'undefined') {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5137/api';
  }
  return `${window.location.origin}/api`;
};

// Get stored password from Zustand store
const getStoredPassword = (): string | null => {
  try {
    const appStorage = localStorage.getItem('app-storage');
    if (!appStorage) return null;
    
    const parsed = JSON.parse(appStorage);
    return parsed.state?.serverPassword || null;
  } catch {
    return null;
  }
};

// Get password from URL params or storage
const getPassword = (): string | null => {
  if (typeof window === 'undefined') return null;
  
  const urlParams = new URLSearchParams(window.location.search);
  const urlPassword = urlParams.get('password');
  const storedPassword = getStoredPassword();
  
  return urlPassword || storedPassword;
};

// Create headers with authorization
const createHeaders = (): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  const password = getPassword();
  if (password) {
    headers.Authorization = password;
  }
  
  return headers;
};

// Generic fetch wrapper with error handling
const apiRequest = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const fullUrl = `${getApiUrl()}${url}`;
  const headers = createHeaders();
  
  const response = await fetch(fullUrl, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  });
  
  // Handle 403 errors
  if (response.status === 403 && typeof window !== 'undefined') {
    window.location.href = '/login';
  }
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response;
};

// API methods
export const APIService = {
  get: async (url: string) => {
    const response = await apiRequest(url);
    const data = await response.json();
    return { data };
  },
  
  post: async (url: string, data?: any) => {
    const response = await apiRequest(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
    
    // Handle empty responses (like post_flags which returns empty string)
    const text = await response.text();
    try {
      return { data: text ? JSON.parse(text) : {} };
    } catch {
      return { data: text };
    }
  },
  
  put: async (url: string, requestData?: any) => {
    const response = await apiRequest(url, {
      method: 'PUT',
      body: requestData ? JSON.stringify(requestData) : undefined,
    });
    const responseData = await response.json();
    return { data: responseData };
  },
  
  delete: async (url: string) => {
    const response = await apiRequest(url, {
      method: 'DELETE',
    });
    const responseData = await response.json();
    return { data: responseData };
  },
};

export default APIService;
