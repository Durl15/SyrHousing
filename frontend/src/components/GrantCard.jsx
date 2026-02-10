import StatusBadge from './StatusBadge';
import DeadlineCountdown from './DeadlineCountdown';

/**
 * GrantCard component
 * Modern card display for grants with status badge and countdown
 */
export default function GrantCard({ program, onClick, matchScore }) {
  const categoryColors = {
    'URGENT SAFETY': 'bg-red-100 text-red-800 border-red-200',
    'HEALTH HAZARDS': 'bg-orange-100 text-orange-800 border-orange-200',
    'AGING IN PLACE': 'bg-purple-100 text-purple-800 border-purple-200',
    'ENERGY & BILLS': 'bg-green-100 text-green-800 border-green-200',
    'HISTORIC RESTORATION': 'bg-amber-100 text-amber-800 border-amber-200',
    'BUYING HELP': 'bg-blue-100 text-blue-800 border-blue-200',
    'GENERAL': 'bg-gray-100 text-gray-800 border-gray-200',
  };

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-200 p-5 cursor-pointer border border-gray-100 hover:border-blue-300"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <h3 className="text-lg font-semibold text-[#1e3a5f] flex-1 leading-tight">
          {program.name}
        </h3>
        <StatusBadge
          deadline={program.status_or_deadline}
          status={program.status_or_deadline}
        />
      </div>

      {/* Match Score (if available) */}
      {matchScore !== undefined && (
        <div className="mb-3">
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2.5">
              <div
                className={`h-2.5 rounded-full ${matchScore >= 75 ? 'bg-green-500' : matchScore >= 50 ? 'bg-yellow-500' : 'bg-gray-400'}`}
                style={{ width: `${matchScore}%` }}
              ></div>
            </div>
            <span className="text-sm font-semibold text-gray-700">{matchScore}%</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">Match score</p>
        </div>
      )}

      {/* Category Badge */}
      <div className="mb-3">
        <span className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${categoryColors[program.menu_category] || categoryColors['GENERAL']}`}>
          {program.menu_category}
        </span>
      </div>

      {/* Benefit Amount */}
      {program.max_benefit && (
        <div className="mb-2">
          <span className="text-sm text-gray-600">Benefit: </span>
          <span className="text-sm font-semibold text-[#2d6a9f]">{program.max_benefit}</span>
        </div>
      )}

      {/* Agency */}
      {program.agency && (
        <div className="mb-2">
          <span className="text-sm text-gray-600">Agency: </span>
          <span className="text-sm text-gray-800">{program.agency}</span>
        </div>
      )}

      {/* Phone */}
      {program.phone && (
        <div className="mb-3">
          <span className="text-sm text-gray-600">Phone: </span>
          <a
            href={`tel:${program.phone}`}
            onClick={(e) => e.stopPropagation()}
            className="text-sm text-[#2d6a9f] hover:underline"
          >
            {program.phone}
          </a>
        </div>
      )}

      {/* Deadline Countdown */}
      {program.status_or_deadline && (
        <DeadlineCountdown deadline={program.status_or_deadline} />
      )}

      {/* Eligibility Preview */}
      {program.eligibility_summary && (
        <p className="text-sm text-gray-600 mt-3 line-clamp-2">
          {program.eligibility_summary}
        </p>
      )}
    </div>
  );
}
