import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5137/api';

export async function GET(request: NextRequest) {
  return handleRequest(request, 'GET');
}

export async function POST(request: NextRequest) {
  return handleRequest(request, 'POST');
}

export async function PUT(request: NextRequest) {
  return handleRequest(request, 'PUT');
}

export async function DELETE(request: NextRequest) {
  return handleRequest(request, 'DELETE');
}

export async function PATCH(request: NextRequest) {
  return handleRequest(request, 'PATCH');
}

async function handleRequest(request: NextRequest, method: string) {
  try {
    // Extract the path from the request URL
    const url = new URL(request.url);
    const pathSegments = url.pathname.split('/api/');
    const backendPath = pathSegments[1] || '';
    
    // Build the backend URL
    const backendUrl = `${API_BASE_URL}/${backendPath}`;
    
    // Prepare headers
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    // Forward authorization header if present
    const authHeader = request.headers.get('authorization');
    if (authHeader) {
      headers.Authorization = authHeader;
    }
    
    // Forward other important headers
    const userAgent = request.headers.get('user-agent');
    if (userAgent) {
      headers['User-Agent'] = userAgent;
    }
    
    const accept = request.headers.get('accept');
    if (accept) {
      headers.Accept = accept;
    }
    
    // Prepare request options
    const requestOptions: RequestInit = {
      method,
      headers,
    };
    
    // Add body for non-GET requests
    if (method !== 'GET') {
      try {
        const body = await request.text();
        if (body) {
          requestOptions.body = body;
        }
      } catch (error) {
        console.error('Error reading request body:', error);
      }
    }
    
    // Forward query parameters
    const queryString = url.search;
    const fullBackendUrl = `${backendUrl}${queryString}`;
    
    // Make request to backend
    const response = await fetch(fullBackendUrl, requestOptions);
    
    // Get response data
    const responseText = await response.text();
    
    // Create response headers
    const responseHeaders = new Headers();
    
    // Forward important response headers
    const contentType = response.headers.get('content-type');
    if (contentType) {
      responseHeaders.set('content-type', contentType);
    }
    
    const cacheControl = response.headers.get('cache-control');
    if (cacheControl) {
      responseHeaders.set('cache-control', cacheControl);
    }
    
    // Return response with same status
    return new NextResponse(responseText, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
    
  } catch (error: any) {
    console.error(`Error proxying ${method} request:`, error.message);
    return NextResponse.json(
      { error: 'Failed to proxy request to backend' },
      { status: 500 }
    );
  }
}
