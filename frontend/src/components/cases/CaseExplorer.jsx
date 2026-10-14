import React, { useState, useMemo } from 'react';
import { 
  Search, Filter, RotateCcw, FolderGit2, ChevronRight, 
  Network, Users, MapPin, Calendar, ShieldAlert, CheckCircle2,
  Clock, AlertCircle, FileText, ChevronLeft, ChevronsLeft, ChevronsRight,
  Loader2, FolderPlus
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';

const OFFENCE_COLORS = {
  'Cyber Crime': 'bg-purple-950/80 text-purple-300 border-purple-500/40',
  'Extortion': 'bg-rose-950/80 text-rose-300 border-rose-500/40',
  'Kidnapping': 'bg-amber-950/80 text-amber-300 border-amber-500/40',
  'Financial Fraud': 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40',
  'Narcotics': 'bg-red-950/80 text-red-300 border-red-500/40',
  'Theft': 'bg-blue-950/80 text-blue-300 border-blue-500/40',
  'Homicide': 'bg-stone-900 text-stone-300 border-stone-600',
  'Smuggling': 'bg-indigo-950/80 text-indigo-300 border-indigo-500/40',
};

export default function CaseExplorer({ cases = [], loading = false, error = null, onSelectCase }) {
  const navigate = useNavigate();
  const { currentUser, role } = useAuth();

  // Search and filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedOffence, setSelectedOffence] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [selectedStation, setSelectedStation] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedYear, setSelectedYear] = useState('');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);

  // Extract unique filter options from dataset
  const filterOptions = useMemo(() => {
    const offences = new Set();
    const districts = new Set();
    const stations = new Set();
    const statuses = new Set();
    const years = new Set();

    cases.forEach((c) => {
      const d = c.details || {};
      if (d.offence_category) offences.add(d.offence_category);
      if (d.district) districts.add(d.district);
      if (d.police_station) stations.add(d.police_station);
      if (d.status) statuses.add(d.status);
      if (d.date_opened) {
        const yr = d.date_opened.split('-')[0];
        if (yr) years.add(yr);
      }
    });

    return {
      offences: Array.from(offences).sort(),
      districts: Array.from(districts).sort(),
      stations: Array.from(stations).sort(),
      statuses: Array.from(statuses).sort(),
      years: Array.from(years).sort().reverse(),
    };
  }, [cases]);

  // Filtered cases
  const filteredCases = useMemo(() => {
    return cases.filter((c) => {
      const d = c.details || {};
      const id = (c.id || '').toLowerCase();
      const title = (d.title || d.case_title || '').toLowerCase();
      const fir = (d.fir_number || '').toLowerCase();
      const desc = (d.description || '').toLowerCase();
      const dist = (d.district || '').toLowerCase();
      const stn = (d.police_station || '').toLowerCase();
      const cat = (d.offence_category || '').toLowerCase();
      const year = d.date_opened ? d.date_opened.split('-')[0] : '';

      // Text query match
      if (searchQuery) {
        const q = searchQuery.toLowerCase().trim();
        const matchesQuery = 
          id.includes(q) || 
          title.includes(q) || 
          fir.includes(q) || 
          desc.includes(q) || 
          dist.includes(q) ||
          stn.includes(q) ||
          cat.includes(q);
        if (!matchesQuery) return false;
      }

      if (selectedOffence && d.offence_category !== selectedOffence) return false;
      if (selectedDistrict && d.district !== selectedDistrict) return false;
      if (selectedStation && d.police_station !== selectedStation) return false;
      if (selectedStatus && d.status !== selectedStatus) return false;
      if (selectedYear && year !== selectedYear) return false;

      return true;
    });
  }, [cases, searchQuery, selectedOffence, selectedDistrict, selectedStation, selectedStatus, selectedYear]);

  // Handle filter changes
  const handleFilterChange = (setter, value) => {
    setter(value);
    setCurrentPage(1);
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedOffence('');
    setSelectedDistrict('');
    setSelectedStation('');
    setSelectedStatus('');
    setSelectedYear('');
    setCurrentPage(1);
  };

  const hasActiveFilters = Boolean(
    searchQuery || selectedOffence || selectedDistrict || selectedStation || selectedStatus || selectedYear
  );

  // Pagination calculations
  const totalPages = Math.ceil(filteredCases.length / pageSize) || 1;
  const paginatedCases = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredCases.slice(start, start + pageSize);
  }, [filteredCases, currentPage, pageSize]);

  // Statistical summary
  const stats = useMemo(() => {
    const total = cases.length;
    let active = 0;
    let closed = 0;
    let withGraph = 0;
    let multiPerson = 0;

    cases.forEach((c) => {
      const d = c.details || {};
      if ((d.status || '').toUpperCase() === 'CLOSED') closed++;
      else active++;

      if (d.has_graph_relationships || (d.evidence_count && d.evidence_count > 0)) {
        withGraph++;
      }
      if (d.associated_persons_count && d.associated_persons_count > 1) {
        multiPerson++;
      }
    });

    return { total, active, closed, withGraph, multiPerson };
  }, [cases]);

  return (
    <div className="space-y-6 select-none animate-fadeIn">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <FolderGit2 className="text-indigo-400" size={22} />
            <h1 className="text-xl font-bold text-slate-100 tracking-wide">
              Case Records Registry
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
              {cases.length} Registered FIRs
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Search, filter, and inspect registered investigation dossiers and relational networks.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/cases/new')}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-lg shadow-indigo-900/30 transition-all cursor-pointer"
            id="btn-register-new-case-explorer"
          >
            <FolderPlus size={15} />
            <span>Register New Case</span>
          </button>
          <div className="text-[11px] text-amber-300/80 bg-amber-950/40 border border-amber-600/30 px-3 py-1.5 rounded-lg max-w-xs text-right hidden sm:block">
            Investigation Registry • Analytical decision support. Requires human verification.
          </div>
        </div>
      </div>

      {/* Officer Jurisdiction & Need-to-Know Scope Banner */}
      {currentUser && (role === 'INVESTIGATING_OFFICER' || role === 'IPS_OFFICER') && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 px-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></span>
            <span className="text-slate-400 font-medium">Jurisdiction Scope:</span>
            <span className="text-slate-100 font-bold font-mono bg-slate-800 px-2.5 py-0.5 rounded border border-slate-700">
              {currentUser.jurisdiction || 'Configured Jurisdiction'}
            </span>
            <span className="text-slate-400 text-[11px]">({currentUser.jurisdiction_level || 'REGIONAL'})</span>
          </div>

          {role === 'INVESTIGATING_OFFICER' && (
            <div className="flex items-center gap-2 text-[11px] text-slate-300">
              <span className="text-slate-400">Need-to-Know Authorization:</span>
              <span className="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/80 font-bold">
                {cases.filter(c => c.is_assigned || c.details?.is_assigned).length} Actively Assigned
              </span>
              <span className="text-slate-500">•</span>
              <span className="px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/80 font-bold">
                {cases.filter(c => c.is_assigned === false || c.details?.is_assigned === false).length} Unassigned In-District
              </span>
            </div>
          )}
        </div>
      )}

      {/* 2. KPI Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Indexed Cases</div>
            <div className="text-2xl font-mono font-bold text-slate-100 mt-0.5">{stats.total}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Complete case inventory</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-slate-400">
            <FileText size={18} />
          </div>
        </div>

        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Active Investigations</div>
            <div className="text-2xl font-mono font-bold text-amber-400 mt-0.5">{stats.active}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">{stats.closed} cases closed</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-amber-400">
            <Clock size={18} />
          </div>
        </div>

        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Network Connected</div>
            <div className="text-2xl font-mono font-bold text-indigo-400 mt-0.5">{stats.withGraph}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Has relational evidence edges</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-indigo-400">
            <Network size={18} />
          </div>
        </div>

        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Multi-Person Cases</div>
            <div className="text-2xl font-mono font-bold text-emerald-400 mt-0.5">{stats.multiPerson}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">≥ 2 linked person leads</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-emerald-400">
            <Users size={18} />
          </div>
        </div>
      </div>

      {/* 3. Search & Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by case title, FIR number, offence, district, or keyword…"
              value={searchQuery}
              onChange={(e) => handleFilterChange(setSearchQuery, e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-700/80 rounded-lg text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {hasActiveFilters && (
            <button
              onClick={handleResetFilters}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-400 bg-slate-800 hover:bg-slate-700 hover:text-slate-200 rounded-lg transition-colors shrink-0"
              title="Reset all filters"
            >
              <RotateCcw size={13} />
              <span>Reset Filters</span>
            </button>
          )}
        </div>

        {/* Filter Dropdowns */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 pt-2 border-t border-slate-800/80">
          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Offence Category
            </label>
            <select
              value={selectedOffence}
              onChange={(e) => handleFilterChange(setSelectedOffence, e.target.value)}
              className="w-full text-xs py-1.5 px-2 bg-slate-950 border border-slate-700/80 rounded-lg text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">All Offences ({filterOptions.offences.length})</option>
              {filterOptions.offences.map((off) => (
                <option key={off} value={off}>{off}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              District
            </label>
            <select
              value={selectedDistrict}
              onChange={(e) => handleFilterChange(setSelectedDistrict, e.target.value)}
              className="w-full text-xs py-1.5 px-2 bg-slate-950 border border-slate-700/80 rounded-lg text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">All Districts ({filterOptions.districts.length})</option>
              {filterOptions.districts.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Police Station
            </label>
            <select
              value={selectedStation}
              onChange={(e) => handleFilterChange(setSelectedStation, e.target.value)}
              className="w-full text-xs py-1.5 px-2 bg-slate-950 border border-slate-700/80 rounded-lg text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 truncate"
            >
              <option value="">All Stations ({filterOptions.stations.length})</option>
              {filterOptions.stations.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Status
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => handleFilterChange(setSelectedStatus, e.target.value)}
              className="w-full text-xs py-1.5 px-2 bg-slate-950 border border-slate-700/80 rounded-lg text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">All Statuses</option>
              {filterOptions.statuses.map((st) => (
                <option key={st} value={st}>{st}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Year
            </label>
            <select
              value={selectedYear}
              onChange={(e) => handleFilterChange(setSelectedYear, e.target.value)}
              className="w-full text-xs py-1.5 px-2 bg-slate-950 border border-slate-700/80 rounded-lg text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">All Years</option>
              {filterOptions.years.map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* 4. Results Header */}
      <div className="flex items-center justify-between text-xs text-slate-400 px-1 font-medium">
        <div>
          Showing <span className="font-bold text-slate-200">{filteredCases.length}</span> matching cases
          {hasActiveFilters && <span className="text-indigo-400 ml-1">(filtered)</span>}
        </div>

        <div className="flex items-center gap-2">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="bg-slate-950 border border-slate-700/80 rounded px-2 py-0.5 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value={10}>10</option>
            <option value={15}>15</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      {/* 5. Case Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-16 flex flex-col items-center justify-center text-slate-400 space-y-3">
            <Loader2 size={32} className="animate-spin text-indigo-400" />
            <p className="text-xs font-semibold">Loading case records…</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center text-red-400 space-y-2">
            <AlertCircle size={28} className="mx-auto" />
            <div className="text-sm font-semibold">{error}</div>
          </div>
        ) : paginatedCases.length === 0 ? (
          <div className="p-16 text-center text-slate-400 space-y-3">
            <FileText size={32} className="mx-auto text-slate-600" />
            <div className="text-slate-300 font-semibold text-sm">No matching case records found</div>
            {hasActiveFilters && (
              <button
                onClick={handleResetFilters}
                className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors font-medium"
              >
                Clear all filters
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-950/80 border-b border-slate-800 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                  <th className="py-3 px-4">Case Title & Offence</th>
                  <th className="py-3 px-4">Case ID / FIR</th>
                  <th className="py-3 px-4">Jurisdiction</th>
                  <th className="py-3 px-4">Year & Station</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {paginatedCases.map((c) => {
                  const d = c.details || {};
                  const offenceClass = OFFENCE_COLORS[d.offence_category] || 'bg-slate-800 text-slate-300 border-slate-700';
                  const isClosed = (d.status || '').toUpperCase() === 'CLOSED';
                  const title = d.title || d.case_title || `Case ${c.id}`;

                  return (
                    <tr
                      key={c.id}
                      onClick={() => onSelectCase(c.id)}
                      className="hover:bg-slate-850/50 cursor-pointer transition-colors group"
                    >
                      {/* Column 1: Human-readable Case Title Prominent */}
                      <td className="py-3.5 px-4 max-w-sm">
                        <div className="font-bold text-slate-100 text-sm group-hover:text-indigo-300 transition-colors">
                          {title}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${offenceClass}`}>
                            {d.offence_category || 'Investigation'}
                          </span>
                          {d.legal_section && (
                            <span className="text-[10px] font-mono text-slate-400">
                              {d.legal_section}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Column 2: Case ID & FIR */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="font-mono font-bold text-xs text-indigo-400">
                          {c.id}
                        </div>
                        <div className="font-mono text-[11px] text-slate-400 mt-0.5">
                          {d.fir_number || 'FIR Unassigned'}
                        </div>
                      </td>

                      {/* Column 3: District */}
                      <td className="py-3.5 px-4 whitespace-nowrap text-xs">
                        <div className="text-slate-200 font-semibold flex items-center gap-1.5">
                          <MapPin size={12} className="text-slate-400 shrink-0" />
                          <span>{d.district || 'General Area'}</span>
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          {d.city || 'State Jurisdiction'}
                        </div>
                      </td>

                      {/* Column 4: Station & Year */}
                      <td className="py-3.5 px-4 whitespace-nowrap text-xs">
                        <div className="text-slate-300">
                          {d.police_station ? `PS: ${d.police_station}` : 'Central PS'}
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                          {d.date_opened || 'Date unrecorded'}
                        </div>
                      </td>

                      {/* Column 5: Status & Assignment */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="flex flex-col gap-1 items-start">
                          <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded uppercase border ${
                            isClosed 
                              ? 'bg-slate-800 text-slate-400 border-slate-700' 
                              : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                          }`}>
                            {d.status || 'ACTIVE'}
                          </span>

                          {role === 'INVESTIGATING_OFFICER' && (
                            c.is_assigned === false || d.is_assigned === false ? (
                              <span className="inline-flex items-center gap-1 text-[9px] font-mono font-bold px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800/80">
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                                UNASSIGNED
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[9px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/80">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                                ASSIGNED
                              </span>
                            )
                          )}
                          {role === 'IPS_OFFICER' && (
                            <span className="inline-flex items-center gap-1 text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/80">
                              SUPERVISORY
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Column 6: Action */}
                      <td className="py-3.5 px-4 whitespace-nowrap text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectCase(c.id);
                          }}
                          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30 transition-all"
                        >
                          <span>Inspect Dossier</span>
                          <ChevronRight size={13} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {!loading && filteredCases.length > 0 && (
          <div className="px-4 py-3 bg-slate-950/70 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <div>
              Page <span className="font-mono font-bold text-slate-200">{currentPage}</span> of{' '}
              <span className="font-mono font-bold text-slate-200">{totalPages}</span>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className="p-1 rounded hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300"
                title="First page"
              >
                <ChevronsLeft size={14} />
              </button>
              <button
                onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="p-1 rounded hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300"
                title="Previous page"
              >
                <ChevronLeft size={14} />
              </button>
              <span className="px-2 font-mono text-slate-300">
                {currentPage}
              </span>
              <button
                onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="p-1 rounded hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300"
                title="Next page"
              >
                <ChevronRight size={14} />
              </button>
              <button
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className="p-1 rounded hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300"
                title="Last page"
              >
                <ChevronsRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
