import { useParams, Link } from 'react-router-dom';

export default function SiteDetail() {
  const { id } = useParams();

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Site Detail: {id}</h2>
      <p className="text-gray-600 mb-4">Detail view placeholder.</p>
      
      <Link to={`/sites/${id}/calibrate`} className="text-blue-600 underline">
        Go to Calibration
      </Link>
    </div>
  );
}
