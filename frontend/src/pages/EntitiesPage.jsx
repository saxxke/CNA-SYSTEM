import React, { useState, useEffect, useMemo } from 'react';
import { 
  Users, Search, Filter, RotateCcw, ChevronRight, 
  MapPin, Phone, Briefcase, FileText, ChevronLeft, 
  ChevronsLeft, ChevronsRight, AlertCircle, Shield, ArrowUpRight,
  Loader2
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';

export default function EntitiesPage() {
  const navigate = useNavigate();

  const [persons, setPersons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Search and filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [selectedGender, setSelectedGender] = useState('');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);

  useEffect(() => {
    let isMounted = true;
    const fetchPersons = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.get('/api/persons');
        if (isMounted) {
          setPersons(res.data);
        }
      } catch (err) {
        if (isMounted) {
          setError('Unable to load person directory from API.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchPersons();
    return () => {
      isMounted = false;
    };
  }, []);

  // Filter options
  const filterOptions = useMemo(() => {
    const districts = new Set();
    const genders = new Set();

    persons.forEach((p) => {
      if (p.district) districts.add(p.district);
      if (p.gender) genders.add(p.gender);
    });

    return {
      districts: Array.from(districts).sort(),
      genders: Array.from(genders).sort(),
    };
  }, [persons]);

  // Filtered persons
  const filteredPersons = useMemo(() => {
    return persons.filter((p) => {
      const q = searchQuery.toLowerCase().trim();
      if (q) {
        const id = (p.person_id || '').toLowerCase();
        const name = (p.full_name || '').toLowerCase();
        const alias = (p.primary_alias || '').toLowerCase();
        const dist = (p.district || '').toLowerCase();
        const occ = (p.occupation || '').toLowerCase();

        const match = id.includes(q) || name.includes(q) || alias.includes(q) || dist.includes(q) || occ.includes(q);
        if (!match) return false;
      }

      if (selectedDistrict && p.district !== selectedDistrict) return false;
      if (selectedGender && p.gender !== selectedGender) return false;

      return true;
    });
  }, [persons, searchQuery, selectedDistrict, selectedGender]);

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedDistrict('');
    setSelectedGender('');
    setCurrentPage(1);
  };

  const hasActiveFilters = Boolean(searchQuery || selectedDistrict || selectedGender);

  // Pagination
  const totalPages = Math.ceil(filteredPersons.length / pageSize) || 1;
  const paginatedPersons = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredPersons.slice(start, start + pageSize);
  }, [filteredPersons, currentPage, pageSize]);

  // Multi-case count
  const multiCaseCount = persons.filter((p) => p.linked_cases_count > 1).length;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 select-none animate-fadeIn">
      {/* 1. Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <Users className="text-sky-400" size={22} />
            <h1 className="text-xl font-bold text-slate-100 tracking-wide">
              Associated Persons Directory
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-sky-950 text-sky-300 border border-sky-800">
              {persons.length} Records
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Comprehensive index of cataloged person identities, associated case files, and telecom identifiers.
          </p>
        </div>

        {/* Safety Disclaimer */}
        <div className="text-[11px] text-amber-300/80 bg-amber-950/40 border border-amber-600/30 px-3 py-1.5 rounded-lg max-w-xs text-right">
          Analytical index • Does not imply guilt or criminal status. Human verification required.
        </div>
      </div>

      {/* 2. Top Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Indexed People</div>
            <div className="text-2xl font-mono font-bold text-slate-100 mt-0.5">{persons.length}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Synthetic cohort individuals</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-sky-400">
            <Users size={18} />
          </div>
        </div>

        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Multi-Case Links</div>
            <div className="text-2xl font-mono font-bold text-indigo-400 mt-0.5">{multiCaseCount}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Associated with ≥ 2 case files</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-indigo-400">
            <FileText size={18} />
          </div>
        </div>

        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Operational Districts</div>
            <div className="text-2xl font-mono font-bold text-emerald-400 mt-0.5">{filterOptions.districts.length}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">State operational areas</div>
          </div>
          <div className="w-10 h-10 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-emerald-400">
            <MapPin size={18} />
          </div>
        </div>
      </div>

      {/* 3. Search & Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative flex-1 w-full">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by person name, alias, occupation, district, or ID…"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-700/80 rounded-lg text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2.5 w-full md:w-auto">
          <select
            value={selectedDistrict}
            onChange={(e) => {
              setSelectedDistrict(e.target.value);
              setCurrentPage(1);
            }}
            className="py-1.5 px-3 bg-slate-950 border border-slate-700/80 rounded-lg text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Districts ({filterOptions.districts.length})</option>
            {filterOptions.districts.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>

          <select
            value={selectedGender}
            onChange={(e) => {
              setSelectedGender(e.target.value);
              setCurrentPage(1);
            }}
            className="py-1.5 px-3 bg-slate-950 border border-slate-700/80 rounded-lg text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Genders</option>
            {filterOptions.genders.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>

          {hasActiveFilters && (
            <button
              onClick={handleResetFilters}
              className="p-2 text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
              title="Reset filters"
            >
              <RotateCcw size={13} />
            </button>
          )}
        </div>
      </div>

      {/* 4. Results Counter */}
      <div className="flex items-center justify-between text-xs text-slate-400 px-1 font-medium">
        <div>
          Showing <span className="font-bold text-slate-200">{filteredPersons.length}</span> matching records
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

      {/* 5. Persons Table — Human-Readable Identities Primary */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-16 flex flex-col items-center justify-center text-slate-400 space-y-3">
            <Loader2 size={32} className="animate-spin text-indigo-400" />
            <p className="text-xs font-semibold">Loading person registry…</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center text-red-400 space-y-2">
            <AlertCircle size={28} className="mx-auto" />
            <div className="text-sm font-semibold">{error}</div>
          </div>
        ) : paginatedPersons.length === 0 ? (
          <div className="p-16 text-center text-slate-400 space-y-3">
            <Users size={32} className="mx-auto text-slate-600" />
            <div className="text-slate-300 font-semibold text-sm">No matching person records found</div>
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
                  <th className="py-3 px-4">Person Identity</th>
                  <th className="py-3 px-4">District / Locality</th>
                  <th className="py-3 px-4">Occupation & Demographics</th>
                  <th className="py-3 px-4">Telecom Identifier</th>
                  <th className="py-3 px-4">Case Involvements</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {paginatedPersons.map((p) => (
                  <tr
                    key={p.person_id}
                    onClick={() => navigate(`/entities/${p.person_id}`)}
                    className="hover:bg-slate-850/50 cursor-pointer transition-colors group"
                  >
                    {/* Column 1: Human-readable Name Prominent, ID secondary */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <div className="font-bold text-slate-100 text-sm group-hover:text-indigo-300 transition-colors">
                        {p.full_name || p.person_id}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="font-mono text-[10px] text-slate-400 font-medium">
                          {p.person_id}
                        </span>
                        {p.primary_alias && (
                          <span className="text-[11px] text-slate-400">
                            • Alias: <span className="text-slate-300 font-medium">"{p.primary_alias}"</span>
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Column 2: District & Locality */}
                    <td className="py-3.5 px-4 whitespace-nowrap text-xs">
                      <div className="text-slate-200 font-semibold flex items-center gap-1.5">
                        <MapPin size={12} className="text-slate-400 shrink-0" />
                        <span>{p.district || 'Headquarters'}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {p.city || 'State Area'}
                      </div>
                    </td>

                    {/* Column 3: Occupation & Demographics */}
                    <td className="py-3.5 px-4 whitespace-nowrap text-xs">
                      <div className="text-slate-200 font-medium">
                        {p.occupation || 'Unspecified'}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {p.gender} {p.age ? `• ${p.age} years` : ''}
                      </div>
                    </td>

                    {/* Column 4: Telecom Identifier */}
                    <td className="py-3.5 px-4 whitespace-nowrap font-mono text-xs text-slate-400">
                      {p.phone_number || 'None on file'}
                    </td>

                    {/* Column 5: Case involvements */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-0.5 rounded-full border ${
                        p.linked_cases_count > 1 
                          ? 'bg-amber-950/80 text-amber-300 border-amber-500/40' 
                          : 'bg-slate-800 text-slate-300 border-slate-700'
                      }`}>
                        <FileText size={11} />
                        <span>{p.linked_cases_count} {p.linked_cases_count === 1 ? 'case' : 'cases'}</span>
                      </span>
                    </td>

                    {/* Column 6: Action */}
                    <td className="py-3.5 px-4 whitespace-nowrap text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/entities/${p.person_id}`);
                        }}
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30 transition-all"
                      >
                        <span>Profile</span>
                        <ChevronRight size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {!loading && filteredPersons.length > 0 && (
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
