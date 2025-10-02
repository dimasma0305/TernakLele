const isDev = process.env.NODE_ENV === 'development';
const serverUrl = isDev ? 'http://127.0.0.1:5137' : process.env.NEXT_PUBLIC_SERVER_URL || '';
const apiUrl = `${serverUrl}/api`;

export const flagsPerPage = 30;
export { apiUrl, serverUrl };