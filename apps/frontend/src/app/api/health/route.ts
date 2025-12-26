import { NextResponse } from 'next/server';

/**
 * Health check endpoint for AWS ALB/ECS
 * Returns 200 OK if the service is healthy
 */
export async function GET() {
  return NextResponse.json(
    {
      status: 'healthy',
      service: 'frontend',
      timestamp: new Date().toISOString(),
    },
    { status: 200 }
  );
}
