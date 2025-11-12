"use client";

export default function TestPage() {
  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Test Page</h1>
        <p className="text-gray-300">This is a simple test page to verify Next.js is working.</p>
        <div className="mt-8">
          <a 
            href="/" 
            className="bg-teal-600 hover:bg-teal-700 text-white px-6 py-3 rounded-lg transition-colors"
          >
            Go to Main App
          </a>
        </div>
      </div>
    </div>
  );
}
