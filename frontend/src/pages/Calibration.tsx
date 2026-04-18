import { useParams } from 'react-router-dom';

export default function Calibration() {
  const { id } = useParams();
  
  return (
    <div className="p-6 text-center">
      <h2 className="text-2xl font-bold mb-4">Site Calibration (Placeholder)</h2>
      <p className="text-gray-600">
        Calibration flow for site <span className="font-mono bg-gray-100 px-1 rounded">{id}</span> is not fully implemented in this MVP.
      </p>
      <p className="text-sm text-gray-500 mt-2">
        See plan.md for future fixed-node computer vision calibration steps.
      </p>
    </div>
  );
}
