import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, data, timestamp } = body;

    console.log('🔍 DEBUG API:', { action, data, timestamp });

    switch (action) {
      case 'log_error':
        return NextResponse.json({
          status: 'logged',
          message: 'Error logged successfully',
          timestamp: new Date().toISOString(),
          error: data
        });

      case 'test_api':
        return NextResponse.json({
          status: 'success',
          message: 'API test successful',
          timestamp: new Date().toISOString(),
          testData: data
        });

      case 'validate_form':
        const validation = validateFormData(data);
        return NextResponse.json({
          status: 'validated',
          message: 'Form validation complete',
          timestamp: new Date().toISOString(),
          validation
        });

      case 'check_health':
        return NextResponse.json({
          status: 'healthy',
          message: 'System health check',
          timestamp: new Date().toISOString(),
          system: {
            nodeVersion: process.version,
            platform: process.platform,
            uptime: process.uptime(),
            memory: process.memoryUsage()
          }
        });

      default:
        return NextResponse.json({
          status: 'unknown_action',
          message: 'Unknown debug action',
          timestamp: new Date().toISOString(),
          availableActions: ['log_error', 'test_api', 'validate_form', 'check_health']
        });
    }

  } catch (error) {
    console.error('❌ DEBUG API Error:', error);
    return NextResponse.json({
      status: 'error',
      message: 'Debug API error',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}

function validateFormData(data: any) {
  const validation = {
    isValid: true,
    errors: [] as string[],
    warnings: [] as string[]
  };

  // Check required fields
  if (!data.text) {
    validation.errors.push('Text field is required');
    validation.isValid = false;
  }

  if (!data.team_member_token) {
    validation.errors.push('Team member token is required');
    validation.isValid = false;
  }

  if (!data.images || data.images.length === 0) {
    validation.errors.push('At least one image is required');
    validation.isValid = false;
  }

  // Check team token validity
  const validTokens = ['mehdi', 'jebbar', 'abde', 'walid'];
  if (data.team_member_token && !validTokens.includes(data.team_member_token)) {
    validation.errors.push(`Invalid team token: ${data.team_member_token}`);
    validation.isValid = false;
  }

  // Check text length
  if (data.text && data.text.length < 10) {
    validation.warnings.push('Text description is very short');
  }

  // Check image count
  if (data.images && data.images.length > 10) {
    validation.warnings.push('Many images uploaded, processing may take longer');
  }

  return validation;
}

export async function GET() {
  return NextResponse.json({
    status: 'debug_api_ready',
    message: 'MAAW Debug API is running',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    endpoints: {
      'POST /api/debug': 'Debug API for error tracking and validation',
      'GET /api/debug': 'Debug API status'
    },
    availableActions: [
      'log_error - Log errors from browser',
      'test_api - Test API connectivity',
      'validate_form - Validate form data',
      'check_health - Check system health'
    ]
  });
}
