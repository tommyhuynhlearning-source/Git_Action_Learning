#!/usr/bin/env bash
set -euo pipefail

aws rds describe-db-instances \
  --db-instance-identifier finance-data \
  --region ap-southeast-1 \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text
