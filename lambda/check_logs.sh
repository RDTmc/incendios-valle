#!/bin/bash
echo "=== Lambda logs: ms-usuarios ==="
LOG_STREAM=$(aws logs describe-log-streams \
    --log-group-name "/aws/lambda/ms-usuarios" \
    --region us-east-1 --order-by LastEventTime \
    --descending --limit 1 \
    --query "logStreams[0].logStreamName" --output text 2>&1)
echo "Stream: $LOG_STREAM"
aws logs get-log-events \
    --log-group-name "/aws/lambda/ms-usuarios" \
    --log-stream-name "$LOG_STREAM" \
    --region us-east-1 \
    --query "events[].message" --output text 2>&1 | head -40

echo ""
echo "=== Lambda logs: ms-incidencias ==="
LOG_STREAM2=$(aws logs describe-log-streams \
    --log-group-name "/aws/lambda/ms-incidencias" \
    --region us-east-1 --order-by LastEventTime \
    --descending --limit 1 \
    --query "logStreams[0].logStreamName" --output text 2>&1)
echo "Stream: $LOG_STREAM2"
aws logs get-log-events \
    --log-group-name "/aws/lambda/ms-incidencias" \
    --log-stream-name "$LOG_STREAM2" \
    --region us-east-1 \
    --query "events[].message" --output text 2>&1 | head -20
