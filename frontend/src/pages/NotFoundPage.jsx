import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center p-4">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-gray-800">404</h1>
        <h2 className="text-4xl font-bold text-gray-700 mt-4">Page Not Found</h2>
        <p className="text-gray-600 mt-2 text-lg">
          The page you are looking for doesn't exist.
        </p>
        <Link
          to="/dashboard"
          className="inline-block mt-8 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition"
        >
          Go to Dashboard
        </Link>
      </div>
    </div>
  );
}