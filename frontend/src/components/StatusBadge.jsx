import { useEffect, useState } from 'react';

/**
 * StatusBadge component
 * Displays grant status with color-coded badges: Open, Closing Soon, Closed
 */
export default function StatusBadge({ deadline, status }) {
  const [badgeInfo, setBadgeInfo] = useState({ text: 'Unknown', color: 'gray' });

  useEffect(() => {
    // Parse deadline/status text to determine badge
    const text = (deadline || status || '').toLowerCase();

    if (text.includes('closed') || text.includes('not accepting') || text.includes('depleted')) {
      setBadgeInfo({ text: 'Closed', color: 'red' });
    } else if (text.includes('waitlist only')) {
      setBadgeInfo({ text: 'Waitlist', color: 'yellow' });
    } else if (text.includes('rolling') || text.includes('year-round') || text.includes('accepting')) {
      setBadgeInfo({ text: 'Open', color: 'green' });
    } else if (text.includes('seasonal') || text.includes('funding cycles')) {
      setBadgeInfo({ text: 'Seasonal', color: 'blue' });
    } else if (text.includes('emergency')) {
      setBadgeInfo({ text: 'Emergency Only', color: 'orange' });
    } else {
      // Try to extract date and calculate if closing soon
      const dateMatch = text.match(/(\d{1,2}\/\d{1,2}\/\d{4}|\d{4}-\d{2}-\d{2}|january|february|march|april|may|june|july|august|september|october|november|december)/i);

      if (dateMatch) {
        // If we find a date, consider it closing soon
        setBadgeInfo({ text: 'Closing Soon', color: 'yellow' });
      } else {
        setBadgeInfo({ text: 'Check Status', color: 'gray' });
      }
    }
  }, [deadline, status]);

  const colorClasses = {
    green: 'bg-green-100 text-green-800 border-green-200',
    yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    red: 'bg-red-100 text-red-800 border-red-200',
    blue: 'bg-blue-100 text-blue-800 border-blue-200',
    orange: 'bg-orange-100 text-orange-800 border-orange-200',
    gray: 'bg-gray-100 text-gray-800 border-gray-200',
  };

  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${colorClasses[badgeInfo.color]}`}>
      {badgeInfo.text}
    </span>
  );
}
