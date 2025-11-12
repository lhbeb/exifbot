import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    message: 'MAAW API is running',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    endpoints: {
      'POST /api/process_product': 'Process product with images and text',
      'GET /api/health': 'Health check endpoint'
    }
  });
}
