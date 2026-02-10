#!/bin/bash

# Setup script for using external database

echo "Setting up external database configuration..."

# Set external DB URL in Pulumi
cd infra
pulumi config set external-db-url "postgresql://postgres:postgres@100.84.171.106:5432/postgres"

echo "✅ Pulumi configured to use external database"
echo ""
echo "Now you can run:"
echo "  pulumi preview  # to see changes"
echo "  pulumi up       # to deploy"
