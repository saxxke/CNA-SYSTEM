import React, { useState, useEffect } from 'react';
import { FolderOpen, Users, Network, Link2, AlertTriangle } from 'lucide-react';
import api from '../../api/client';
import StatCard from '../common/StatCard';

export default function DashboardOverview({ onPriorityCountLoaded }) {
  const [data, setData] = useState(null);
  const [priorityCount, setPriorityCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const fetchSummary = async () => {
      try {
        setLoading(true);
        const [sumRes, prioRes] = await Promise.all([
          api.get('/api/summary'),
          api.get('/api/priority?limit=100').catch(() => ({ data: [] }))
        ]);
        if (isMounted) {
          setData(sumRes.data);
          const pCount = (prioRes.data || []).length;
          setPriorityCount(pCount);
          onPriorityCountLoaded?.(pCount);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to connect to API');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };
    
    fetchSummary();
    return () => {
      isMounted = false;
    };
  }, [onPriorityCountLoaded]);

  // Derive persons count from node_counts_by_type if available
  const personCount = data?.node_counts_by_type?.PERSON || data?.total_entities || 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 select-none">
      <StatCard 
        title="Case Records" 
        value={data?.total_cases || 0} 
        subtitle="Registered FIR dossiers"
        icon={FolderOpen} 
        loading={loading} 
        error={error} 
      />
      <StatCard 
        title="Associated People" 
        value={personCount} 
        subtitle="Cataloged identities"
        icon={Users} 
        loading={loading} 
        error={error} 
      />
      <StatCard 
        title="Network Entities" 
        value={data?.total_network_nodes || 0} 
        subtitle="Phones, accounts, vehicles"
        icon={Network} 
        loading={loading} 
        error={error} 
      />
      <StatCard 
        title="Relationships" 
        value={data?.total_relationships || 0} 
        subtitle="Validated evidence edges"
        icon={Link2} 
        loading={loading} 
        error={error} 
      />
      <StatCard 
        title="Priority Leads" 
        value={priorityCount} 
        subtitle="Algorithmic triage leads"
        icon={AlertTriangle} 
        loading={loading} 
        error={error} 
      />
    </div>
  );
}
