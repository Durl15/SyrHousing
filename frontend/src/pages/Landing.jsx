import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Landing() {
  const { user } = useAuth();

  return (
    <div className="min-h-[calc(100vh-8rem)]">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-[#1e3a5f] via-[#2d6a9f] to-[#1e3a5f] text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-28">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            <div className="flex-1 text-center lg:text-left">
              <div className="text-sm font-semibold tracking-widest uppercase text-[#c9a84c] mb-4">
                DJ AI Business Consultant
              </div>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
                Syracuse Housing
                <span className="block text-[#4a9eda]">Grant Discovery</span>
              </h1>
              <p className="text-lg sm:text-xl text-blue-100 mb-8 max-w-2xl">
                AI-powered tool helping Syracuse seniors and homeowners discover
                home repair grants, screen eligibility, and track applications
                — all in one place.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                {user ? (
                  <Link
                    to="/dashboard"
                    className="px-8 py-3 bg-[#c9a84c] text-[#1e3a5f] font-semibold rounded-lg hover:bg-[#d4b85d] transition-colors text-center no-underline"
                  >
                    Go to Dashboard
                  </Link>
                ) : (
                  <>
                    <Link
                      to="/register"
                      className="px-8 py-3 bg-[#c9a84c] text-[#1e3a5f] font-semibold rounded-lg hover:bg-[#d4b85d] transition-colors text-center no-underline"
                    >
                      Get Started Free
                    </Link>
                    <Link
                      to="/login"
                      className="px-8 py-3 border-2 border-white/30 text-white font-semibold rounded-lg hover:bg-white/10 transition-colors text-center no-underline"
                    >
                      Sign In
                    </Link>
                  </>
                )}
              </div>
            </div>
            <div className="flex-shrink-0">
              <img
                src="/phoenix-logo.png"
                alt="Phoenix"
                className="w-48 h-48 sm:w-64 sm:h-64 object-contain opacity-20 lg:opacity-30"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-[#1e3a5f] mb-12">
            How It Works
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: '🔍',
                title: 'Discover Programs',
                desc: 'Browse 20+ Syracuse-area housing repair grants, loans, and assistance programs curated for seniors and homeowners.',
              },
              {
                icon: '🤖',
                title: 'AI Eligibility Screening',
                desc: 'Our AI analyzes your home profile and repair needs to rank programs by relevance and match likelihood.',
              },
              {
                icon: '📋',
                title: 'Track Applications',
                desc: 'Keep track of which programs you\'ve applied to, documents needed, and deadlines — all in your dashboard.',
              },
            ].map((f) => (
              <div
                key={f.title}
                className="bg-white rounded-xl shadow-md p-8 text-center hover:shadow-lg transition-shadow"
              >
                <div className="text-4xl mb-4">{f.icon}</div>
                <h3 className="text-xl font-semibold text-[#1e3a5f] mb-3">{f.title}</h3>
                <p className="text-gray-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-[#f1f5f9] py-16">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-[#1e3a5f] mb-4">
            Ready to find your grants?
          </h2>
          <p className="text-gray-600 mb-8">
            Free for Syracuse-area homeowners. No credit card required.
          </p>
          {!user && (
            <Link
              to="/register"
              className="inline-block px-8 py-3 bg-[#1e3a5f] text-white font-semibold rounded-lg hover:bg-[#2d6a9f] transition-colors no-underline"
            >
              Create Your Free Account
            </Link>
          )}
        </div>
      </section>
    </div>
  );
}
