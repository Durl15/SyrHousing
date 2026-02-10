export default function Footer() {
  return (
    <footer className="bg-[#0f172a] text-gray-400 py-8 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img
              src="/phoenix-logo.png"
              alt=""
              className="h-8 w-8 object-contain opacity-50"
            />
            <div>
              <div className="text-sm text-gray-300 font-medium">DJ AI Business Consultant</div>
              <div className="text-xs">Transforming Business. Rising Above the Challenges.</div>
            </div>
          </div>
          <div className="text-xs text-center sm:text-right">
            <div>Syracuse Housing Grant Discovery Tool</div>
            <div className="mt-1">Helping seniors and homeowners find home repair assistance</div>
          </div>
        </div>
      </div>
    </footer>
  );
}
