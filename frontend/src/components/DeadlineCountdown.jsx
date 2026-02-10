import { useEffect, useState } from 'react';

/**
 * DeadlineCountdown component
 * Displays countdown timer for grant deadlines
 */
export default function DeadlineCountdown({ deadline }) {
  const [countdown, setCountdown] = useState(null);

  useEffect(() => {
    if (!deadline) return;

    const parseDeadline = (text) => {
      // Try to extract a date from the deadline text
      const datePatterns = [
        // MM/DD/YYYY
        /(\d{1,2})\/(\d{1,2})\/(\d{4})/,
        // YYYY-MM-DD
        /(\d{4})-(\d{2})-(\d{2})/,
        // Month Day, Year
        /(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})/i,
      ];

      for (const pattern of datePatterns) {
        const match = text.match(pattern);
        if (match) {
          let date;
          if (pattern === datePatterns[0]) {
            // MM/DD/YYYY
            date = new Date(match[3], match[1] - 1, match[2]);
          } else if (pattern === datePatterns[1]) {
            // YYYY-MM-DD
            date = new Date(match[1], match[2] - 1, match[3]);
          } else if (pattern === datePatterns[2]) {
            // Month Day, Year
            const months = {
              january: 0, february: 1, march: 2, april: 3, may: 4, june: 5,
              july: 6, august: 7, september: 8, october: 9, november: 10, december: 11
            };
            date = new Date(match[3], months[match[1].toLowerCase()], match[2]);
          }

          if (date && !isNaN(date.getTime())) {
            return date;
          }
        }
      }
      return null;
    };

    const deadlineDate = parseDeadline(deadline.toLowerCase());

    if (!deadlineDate) {
      setCountdown(null);
      return;
    }

    const updateCountdown = () => {
      const now = new Date();
      const diff = deadlineDate - now;

      if (diff <= 0) {
        setCountdown({ expired: true });
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

      setCountdown({ days, hours, expired: false });
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000 * 60 * 60); // Update every hour

    return () => clearInterval(interval);
  }, [deadline]);

  if (!countdown) return null;

  if (countdown.expired) {
    return (
      <div className="text-red-600 text-sm font-medium">
        ⏰ Deadline passed
      </div>
    );
  }

  const isUrgent = countdown.days <= 7;
  const isWarning = countdown.days <= 30 && countdown.days > 7;

  return (
    <div className={`text-sm font-medium ${isUrgent ? 'text-red-600' : isWarning ? 'text-yellow-600' : 'text-blue-600'}`}>
      {isUrgent && '🔴 '}
      {isWarning && '⚠️ '}
      {countdown.days > 0 && (
        <>
          {countdown.days} day{countdown.days !== 1 ? 's' : ''} left
        </>
      )}
      {countdown.days === 0 && (
        <>
          {countdown.hours} hour{countdown.hours !== 1 ? 's' : ''} left
        </>
      )}
    </div>
  );
}
