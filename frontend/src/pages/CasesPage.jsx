import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/client';
import CaseExplorer from '../components/cases/CaseExplorer';
import CaseDetails from '../components/cases/CaseDetails';

export default function CasesPage() {
  const { caseId } = useParams();
  const navigate = useNavigate();

  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const fetchCases = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.get('/api/cases');
        if (isMounted) {
          setCases(res.data);
        }
      } catch (err) {
        if (isMounted) {
          setError('Unable to connect to the case registry API. Ensure backend is running.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchCases();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSelectCase = (id) => {
    navigate(`/cases/${id}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToExplorer = () => {
    navigate('/cases');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {caseId ? (
        <CaseDetails
          caseId={caseId}
          onBack={handleBackToExplorer}
          onSelectCase={handleSelectCase}
        />
      ) : (
        <CaseExplorer
          cases={cases}
          loading={loading}
          error={error}
          onSelectCase={handleSelectCase}
        />
      )}
    </div>
  );
}
