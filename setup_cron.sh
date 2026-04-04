#!/bin/bash
# Add this to crontab on the server for daily 6am KST email digest
# Run: crontab -e
# Add this line (6am KST = 9pm UTC previous day):
# 0 21 * * * cd /app && python3 src/send_digest.py >> /var/log/mochi-digest.log 2>&1

echo "To set up the daily digest cron job, run:"
echo "  crontab -e"
echo "Then add this line:"
echo '  0 21 * * * cd /app && python3 src/send_digest.py >> /var/log/mochi-digest.log 2>&1'
echo ""
echo "This runs at 9pm UTC = 6am KST next day"
