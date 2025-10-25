import { useParams } from 'react-router-dom';

export default function LetterDetailPage() {
  const { id } = useParams();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Letter Details</h1>
        <p className="mt-2 text-gray-600">Letter ID: {id}</p>
      </div>
      <div className="card">
        <p className="text-gray-600">Letter details coming soon...</p>
      </div>
    </div>
  );
}
