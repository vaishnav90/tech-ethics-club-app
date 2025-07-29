#!/bin/bash
# Setup script to configure the environment for Cloud Storage access

echo "🔧 Setting up environment for Cloud Storage access..."

# Set the environment variable for the current session
export GOOGLE_APPLICATION_CREDENTIALS="/Users/vaishnavanand/club2/tech-ethics-club-sa-key.json"

echo "✅ Set GOOGLE_APPLICATION_CREDENTIALS to: $GOOGLE_APPLICATION_CREDENTIALS"

# Verify the file exists
if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✅ Service account key file exists"
else
    echo "❌ Service account key file not found: $GOOGLE_APPLICATION_CREDENTIALS"
    exit 1
fi

# Test the configuration
echo "🧪 Testing configuration..."
python3 -c "
import os
from google.cloud import storage

try:
    client = storage.Client()
    project = client.project
    credentials = client._credentials
    
    print(f'✅ Successfully connected to project: {project}')
    
    if hasattr(credentials, 'service_account_email'):
        print(f'✅ Using service account: {credentials.service_account_email}')
    else:
        print('⚠️  Not using service account credentials')
        
    # Test bucket access
    bucket = client.bucket('tech-ethics-club-uploads')
    if bucket.exists():
        print('✅ Can access Cloud Storage bucket')
    else:
        print('❌ Cannot access Cloud Storage bucket')
        
except Exception as e:
    print(f'❌ Error testing configuration: {e}')
"

echo ""
echo "🎉 Environment setup complete!"
echo ""
echo "📋 To make this permanent, add this line to your ~/.zshrc file:"
echo "export GOOGLE_APPLICATION_CREDENTIALS=\"/Users/vaishnavanand/club2/tech-ethics-club-sa-key.json\""
echo ""
echo "🔗 Your app is running at: http://localhost:5001"
echo "🌐 Your deployed app is at: https://techandethics.wl.r.appspot.com/"
echo ""
echo "✅ Both environments should now see the same Cloud Storage data!" 