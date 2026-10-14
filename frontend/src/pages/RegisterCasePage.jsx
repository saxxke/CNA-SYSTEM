import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FolderPlus, UserPlus, Link2, ShieldAlert, CheckCircle2, 
  AlertCircle, ChevronRight, ChevronLeft, ArrowRight, User, 
  Search, Trash2, Plus, Sparkles, Network, FileText, Phone,
  Building, Car, MapPin, Loader2, RotateCcw, AlertTriangle, X
} from 'lucide-react';
import api from '../api/client';

const OFFENCE_CATEGORIES = [
  'Kidnapping', 'Extortion', 'Cybercrime', 'Financial Fraud', 'Theft',
  'Robbery', 'Burglary', 'Assault', 'Criminal Intimidation', 'Property Offence',
  'Murder', 'Attempted Murder', 'Molestation', 'Forgery', 'Fraud',
  'Narcotics', 'Smuggling', 'Other'
];

const ROLES = [
  { value: 'SUBJECT', label: 'Subject of Investigation' },
  { value: 'PERSON_OF_INTEREST', label: 'Person of Interest' },
  { value: 'WITNESS', label: 'Witness' },
  { value: 'VICTIM', label: 'Victim' },
  { value: 'COMPLAINANT', label: 'Complainant' },
  { value: 'INFORMANT', label: 'Informant' },
  { value: 'OTHER', label: 'Other Associate' }
];

export default function RegisterCasePage() {
  const navigate = useNavigate();

  // Stepper state: 1 = Case Details, 2 = People, 3 = Optional Entities, 4 = Review, 5 = Confirmation
  const [currentStep, setCurrentStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [saveResult, setSaveResult] = useState(null);

  // Dynamic next IDs preview
  const [nextCaseId, setNextCaseId] = useState('');
  const [nextPersonId, setNextPersonId] = useState('');

  // Step 1: Case Details
  const [caseData, setCaseData] = useState({
    title: '',
    offence_category: 'Kidnapping',
    incident_date: new Date().toISOString().split('T')[0],
    police_station: 'Fictional PS No. 1, Raipur',
    district: 'Raipur',
    location: 'Raipur Market Area',
    status: 'OPEN',
    fir_number: '',
    legal_section: 'IPC 363',
    incident_time: '',
    state: 'Chhattisgarh',
    description: ''
  });
  const [caseErrors, setCaseErrors] = useState({});

  // Step 2: Associated People
  const [associatedPersons, setAssociatedPersons] = useState([]);
  const [peopleTab, setPeopleTab] = useState('search'); // 'search' or 'new'
  
  // Person search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // New person form
  const [newPerson, setNewPerson] = useState({
    full_name: '',
    gender: 'Male',
    date_of_birth: '',
    occupation: '',
    phone: '',
    email: '',
    address: '',
    district: 'Raipur',
    locality: ''
  });
  const [newPersonErrors, setNewPersonErrors] = useState({});
  const [selectedRole, setSelectedRole] = useState('PERSON_OF_INTEREST');

  // Duplicate Check Modal State
  const [duplicateModal, setDuplicateModal] = useState({
    isOpen: false,
    checking: false,
    matches: [],
    pendingPersonData: null,
    pendingRole: 'PERSON_OF_INTEREST'
  });

  // Step 3: Optional Entities
  const [optionalEntities, setOptionalEntities] = useState([]);
  const [entityInput, setEntityInput] = useState({
    entity_type: 'PHONE',
    value: '',
    vehicle_type: 'Four Wheeler',
    bank_name: 'State Bank of India'
  });

  // Fetch next IDs on mount
  useEffect(() => {
    api.get('/api/cases/next-id')
      .then(res => setNextCaseId(res.data.next_case_id))
      .catch(() => {});
    api.get('/api/persons/next-id')
      .then(res => setNextPersonId(res.data.next_person_id))
      .catch(() => {});
  }, []);

  // Live search for existing persons
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        setSearchLoading(true);
        const res = await api.get(`/api/persons/search-linking?q=${encodeURIComponent(searchQuery)}`);
        setSearchResults(res.data);
      } catch (err) {
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Validation: Step 1
  const validateStep1 = () => {
    const errs = {};
    if (!caseData.title.trim()) errs.title = 'Case title is required.';
    if (!caseData.offence_category) errs.offence_category = 'Offence category is required.';
    if (!caseData.incident_date) errs.incident_date = 'Incident date is required.';
    if (!caseData.police_station.trim()) errs.police_station = 'Police station is required.';
    if (!caseData.district.trim()) errs.district = 'District is required.';
    if (!caseData.location.trim()) errs.location = 'Incident location is required.';
    if (!caseData.description.trim()) errs.description = 'Case narrative description is required.';
    setCaseErrors(errs);
    return Object.keys(errs).length === 0;
  };

  // Add existing person
  const handleLinkExistingPerson = (person) => {
    if (associatedPersons.some(p => p.person_id === person.person_id)) {
      alert(`Person ${person.person_id} is already linked to this case.`);
      return;
    }
    setAssociatedPersons(prev => [
      ...prev,
      {
        person_type: 'EXISTING',
        person_id: person.person_id,
        full_name: person.full_name,
        district: person.district,
        occupation: person.occupation,
        phone_number: person.phone_number,
        role: selectedRole
      }
    ]);
    setSearchQuery('');
    setSearchResults([]);
  };

  // Trigger duplicate check before adding new person
  const handleCheckAndAddNewPerson = async () => {
    const errs = {};
    if (!newPerson.full_name.trim()) errs.full_name = 'Full name is required.';
    setNewPersonErrors(errs);
    if (Object.keys(errs).length > 0) return;

    try {
      setDuplicateModal(prev => ({ ...prev, checking: true }));
      const res = await api.post('/api/persons/check-duplicate', {
        full_name: newPerson.full_name,
        phone: newPerson.phone || undefined,
        district: newPerson.district || undefined
      });

      if (res.data.has_matches && res.data.matches.length > 0) {
        // Show advisory warning modal
        setDuplicateModal({
          isOpen: true,
          checking: false,
          matches: res.data.matches,
          pendingPersonData: { ...newPerson },
          pendingRole: selectedRole
        });
      } else {
        // No duplicate matches, directly add
        commitAddNewPerson(newPerson, selectedRole);
        setDuplicateModal(prev => ({ ...prev, checking: false }));
      }
    } catch (err) {
      commitAddNewPerson(newPerson, selectedRole);
      setDuplicateModal(prev => ({ ...prev, checking: false }));
    }
  };

  // Commit new person to list
  const commitAddNewPerson = (personPayload, role) => {
    setAssociatedPersons(prev => [
      ...prev,
      {
        person_type: 'NEW',
        person_id: null,
        full_name: personPayload.full_name,
        district: personPayload.district,
        occupation: personPayload.occupation || 'Not Specified',
        phone_number: personPayload.phone || '',
        new_person_data: { ...personPayload },
        role: role
      }
    ]);
    // Reset form
    setNewPerson({
      full_name: '',
      gender: 'Male',
      date_of_birth: '',
      occupation: '',
      phone: '',
      email: '',
      address: '',
      district: caseData.district || 'Raipur',
      locality: ''
    });
    setNewPersonErrors({});
    setDuplicateModal({ isOpen: false, checking: false, matches: [], pendingPersonData: null, pendingRole: 'PERSON_OF_INTEREST' });
  };

  const handleRemovePerson = (idx) => {
    setAssociatedPersons(prev => prev.filter((_, i) => i !== idx));
  };

  const handleUpdateRole = (idx, newRole) => {
    setAssociatedPersons(prev => prev.map((p, i) => i === idx ? { ...p, role: newRole } : p));
  };

  // Add optional entity
  const handleAddEntity = () => {
    if (!entityInput.value.trim()) return;
    setOptionalEntities(prev => [...prev, { ...entityInput }]);
    setEntityInput({
      entity_type: 'PHONE',
      value: '',
      vehicle_type: 'Four Wheeler',
      bank_name: 'State Bank of India'
    });
  };

  const handleRemoveEntity = (idx) => {
    setOptionalEntities(prev => prev.filter((_, i) => i !== idx));
  };

  // Final Submit
  const handleFinalSave = async () => {
    setSaving(true);
    setSaveError(null);

    const payload = {
      case: {
        title: caseData.title,
        offence_category: caseData.offence_category,
        incident_date: caseData.incident_date,
        location: caseData.location,
        district: caseData.district,
        police_station: caseData.police_station,
        description: caseData.description,
        status: caseData.status,
        fir_number: caseData.fir_number || undefined,
        legal_section: caseData.legal_section || undefined,
        incident_time: caseData.incident_time || undefined,
        state: caseData.state,
        additional_notes: caseData.additional_notes || undefined
      },
      associated_persons: associatedPersons.map(p => ({
        person_type: p.person_type,
        role: p.role,
        person_id: p.person_id || undefined,
        new_person_data: p.new_person_data || undefined
      })),
      optional_entities: optionalEntities.map(e => ({
        entity_type: e.entity_type,
        value: e.value,
        vehicle_type: e.vehicle_type,
        bank_name: e.bank_name
      }))
    };

    try {
      const res = await api.post('/api/cases/register', payload);
      setSaveResult(res.data);
      setCurrentStep(5); // Show confirmation
    } catch (err) {
      const errorMsg = err.response?.data?.detail?.message || err.response?.data?.detail || err.message || 'Failed to register case record.';
      const errList = err.response?.data?.detail?.errors || [];
      setSaveError(errList.length > 0 ? errList.join(' • ') : errorMsg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Title & Safety Notice */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <FolderPlus size={20} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
                Register New Case Record
                {nextCaseId && (
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    Expected: {nextCaseId}
                  </span>
                )}
              </h1>
              <p className="text-xs text-slate-400">
                Controlled synthetic investigation data registration • Fictional demonstration environment
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => navigate('/cases')}
          className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-all"
        >
          Cancel & Return
        </button>
      </div>

      {/* Stepper Navigation */}
      {currentStep < 5 && (
        <div className="grid grid-cols-4 gap-2 bg-slate-900/80 p-2 rounded-xl border border-slate-800 text-xs select-none">
          {[
            { num: 1, label: 'Case Details' },
            { num: 2, label: 'Associated People' },
            { num: 3, label: 'Optional Entities' },
            { num: 4, label: 'Review & Confirm' },
          ].map(s => (
            <button
              key={s.num}
              onClick={() => {
                if (s.num === 1) setCurrentStep(1);
                else if (s.num === 2 && validateStep1()) setCurrentStep(2);
                else if (s.num === 3 && validateStep1() && associatedPersons.length > 0) setCurrentStep(3);
                else if (s.num === 4 && validateStep1() && associatedPersons.length > 0) setCurrentStep(4);
              }}
              className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg font-semibold transition-all ${
                currentStep === s.num
                  ? 'bg-indigo-600 text-white shadow-md'
                  : currentStep > s.num
                  ? 'bg-slate-800 text-slate-200 hover:bg-slate-750'
                  : 'text-slate-500 hover:text-slate-400'
              }`}
            >
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                currentStep === s.num ? 'bg-white text-indigo-600' : 'bg-slate-700 text-slate-300'
              }`}>
                {s.num}
              </span>
              <span className="hidden sm:inline">{s.label}</span>
            </button>
          ))}
        </div>
      )}

      {/* ================= STEP 1: CASE DETAILS ================= */}
      {currentStep === 1 && (
        <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 space-y-6 shadow-xl">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <FileText size={18} className="text-indigo-400" />
              Step 1 — Case Information
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Enter official investigation record parameters and initial case narrative.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Case Title */}
            <div className="md:col-span-2 space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>Case Title *</span>
                {caseErrors.title && <span className="text-red-400 text-[11px]">{caseErrors.title}</span>}
              </label>
              <input
                type="text"
                value={caseData.title}
                onChange={e => setCaseData({ ...caseData, title: e.target.value })}
                placeholder="e.g. Kidnapping Investigation — Raipur Market"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Offence Category */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Offence Category *</label>
              <select
                value={caseData.offence_category}
                onChange={e => setCaseData({ ...caseData, offence_category: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              >
                {OFFENCE_CATEGORIES.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            {/* Status */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Case Status *</label>
              <select
                value={caseData.status}
                onChange={e => setCaseData({ ...caseData, status: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              >
                <option value="OPEN">OPEN</option>
                <option value="UNDER INVESTIGATION">UNDER INVESTIGATION</option>
                <option value="CHARGESHEETED">CHARGESHEETED</option>
                <option value="CLOSED">CLOSED</option>
              </select>
            </div>

            {/* Incident Date */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>Incident Date *</span>
                {caseErrors.incident_date && <span className="text-red-400 text-[11px]">{caseErrors.incident_date}</span>}
              </label>
              <input
                type="date"
                value={caseData.incident_date}
                onChange={e => setCaseData({ ...caseData, incident_date: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* FIR Number */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                FIR Number (Optional)
              </label>
              <input
                type="text"
                value={caseData.fir_number}
                onChange={e => setCaseData({ ...caseData, fir_number: e.target.value })}
                placeholder="e.g. FIR-SYNTH-RAI-0251"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Police Station */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>Police Station *</span>
                {caseErrors.police_station && <span className="text-red-400 text-[11px]">{caseErrors.police_station}</span>}
              </label>
              <input
                type="text"
                value={caseData.police_station}
                onChange={e => setCaseData({ ...caseData, police_station: e.target.value })}
                placeholder="e.g. Fictional PS No. 1, Raipur"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* District */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>District *</span>
                {caseErrors.district && <span className="text-red-400 text-[11px]">{caseErrors.district}</span>}
              </label>
              <input
                type="text"
                value={caseData.district}
                onChange={e => setCaseData({ ...caseData, district: e.target.value })}
                placeholder="e.g. Raipur"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Location */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>Location / Locality *</span>
                {caseErrors.location && <span className="text-red-400 text-[11px]">{caseErrors.location}</span>}
              </label>
              <input
                type="text"
                value={caseData.location}
                onChange={e => setCaseData({ ...caseData, location: e.target.value })}
                placeholder="e.g. Raipur Industrial Area"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Legal Section */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Legal Section</label>
              <input
                type="text"
                value={caseData.legal_section}
                onChange={e => setCaseData({ ...caseData, legal_section: e.target.value })}
                placeholder="e.g. IPC 363, IPC 384"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Case Narrative Description */}
            <div className="md:col-span-2 space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>Investigation Narrative / Description *</span>
                {caseErrors.description && <span className="text-red-400 text-[11px]">{caseErrors.description}</span>}
              </label>
              <textarea
                rows={3}
                value={caseData.description}
                onChange={e => setCaseData({ ...caseData, description: e.target.value })}
                placeholder="Detailed investigative summary of the incident and registered findings..."
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-800">
            <button
              onClick={() => {
                if (validateStep1()) setCurrentStep(2);
              }}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg cursor-pointer"
            >
              <span>Continue to Associated People</span>
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* ================= STEP 2: ASSOCIATED PEOPLE ================= */}
      {currentStep === 2 && (
        <div className="space-y-6">
          {/* People Selection Panel */}
          <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 space-y-5 shadow-xl">
            <div className="border-b border-slate-800 pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <UserPlus size={18} className="text-indigo-400" />
                  Step 2 — Associated People
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Search existing persons to link, or record a new person with advisory duplicate protection.
                </p>
              </div>

              {/* Mode Toggle */}
              <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800">
                <button
                  onClick={() => setPeopleTab('search')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    peopleTab === 'search' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Search size={13} />
                  <span>Search Existing</span>
                </button>
                <button
                  onClick={() => setPeopleTab('new')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    peopleTab === 'new' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <UserPlus size={13} />
                  <span>Create New Person</span>
                </button>
              </div>
            </div>

            {/* Role selector to assign */}
            <div className="flex items-center gap-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
              <span className="text-xs font-semibold text-slate-300 whitespace-nowrap">
                Default Association Role:
              </span>
              <select
                value={selectedRole}
                onChange={e => setSelectedRole(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
              >
                {ROLES.map(r => (
                  <option key={r.value} value={r.value}>{r.label} ({r.value})</option>
                ))}
              </select>
              <span className="text-[11px] text-slate-500 hidden md:inline">
                • Can be adjusted individually per person below.
              </span>
            </div>

            {/* TAB A: Search Existing */}
            {peopleTab === 'search' && (
              <div className="space-y-4">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    placeholder="Search by full name (e.g. Arjun Mehta), Person ID (PERSON-001), phone, or alias…"
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                  {searchLoading && (
                    <Loader2 className="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-indigo-400 animate-spin" />
                  )}
                </div>

                {/* Results List */}
                {searchResults.length > 0 && (
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {searchResults.map(p => (
                      <div
                        key={p.person_id}
                        className="flex items-center justify-between p-3 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-slate-700 transition-all"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 font-bold text-xs">
                            {p.full_name[0]}
                          </div>
                          <div>
                            <div className="text-xs font-bold text-slate-200 flex items-center gap-2">
                              <span>{p.full_name}</span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                                {p.person_id}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-400 mt-0.5">
                              {p.district || 'Raipur'} • {p.occupation || 'Associate'} • {p.phone_number || 'No phone'}
                              <span className="ml-2 px-1.5 py-0.2 rounded text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-800/40">
                                {p.associated_case_count} linked cases
                              </span>
                            </div>
                          </div>
                        </div>

                        <button
                          onClick={() => handleLinkExistingPerson(p)}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/40 text-indigo-300 text-xs font-semibold transition-all cursor-pointer"
                        >
                          <Link2 size={13} />
                          <span>Link Person</span>
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                {searchQuery.length >= 2 && searchResults.length === 0 && !searchLoading && (
                  <div className="text-center py-6 text-xs text-slate-500 bg-slate-950/40 rounded-xl border border-slate-800">
                    No matching persons found. Switch to "Create New Person" if registering a new individual.
                  </div>
                )}
              </div>
            )}

            {/* TAB B: Create New Person Form */}
            {peopleTab === 'new' && (
              <div className="space-y-4 bg-slate-950/50 p-4 rounded-xl border border-slate-800">
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {/* Full Name */}
                  <div className="sm:col-span-2 space-y-1">
                    <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                      <span>Full Name *</span>
                      {newPersonErrors.full_name && <span className="text-red-400 text-[10px]">{newPersonErrors.full_name}</span>}
                    </label>
                    <input
                      type="text"
                      value={newPerson.full_name}
                      onChange={e => setNewPerson({ ...newPerson, full_name: e.target.value })}
                      placeholder="e.g. Rahul Verma"
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  {/* Gender */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-300">Gender</label>
                    <select
                      value={newPerson.gender}
                      onChange={e => setNewPerson({ ...newPerson, gender: e.target.value })}
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                      <option value="Unknown">Unknown</option>
                    </select>
                  </div>

                  {/* Phone */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-300">Phone Number</label>
                    <input
                      type="text"
                      value={newPerson.phone}
                      onChange={e => setNewPerson({ ...newPerson, phone: e.target.value })}
                      placeholder="e.g. 9876543210"
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  {/* Occupation */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-300">Occupation</label>
                    <input
                      type="text"
                      value={newPerson.occupation}
                      onChange={e => setNewPerson({ ...newPerson, occupation: e.target.value })}
                      placeholder="e.g. Trader, Clerk"
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  {/* District */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-300">District</label>
                    <input
                      type="text"
                      value={newPerson.district}
                      onChange={e => setNewPerson({ ...newPerson, district: e.target.value })}
                      placeholder="e.g. Raipur"
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    onClick={handleCheckAndAddNewPerson}
                    disabled={duplicateModal.checking}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all cursor-pointer"
                  >
                    {duplicateModal.checking ? (
                      <Loader2 size={14} className="animate-spin" />
                    ) : (
                      <Plus size={14} />
                    )}
                    <span>Check & Add Person</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Added Persons List */}
          <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <span>Associated People In This Record</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono">
                  {associatedPersons.length}
                </span>
              </h3>
              <span className="text-[11px] text-slate-400">
                Minimum 1 associated person required
              </span>
            </div>

            {associatedPersons.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500 bg-slate-950/40 rounded-xl border border-slate-800">
                No people associated yet. Search an existing person or create a new person above.
              </div>
            ) : (
              <div className="space-y-2">
                {associatedPersons.map((p, idx) => (
                  <div
                    key={p.person_id || p.full_name + idx}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-slate-700 transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-xs">
                        {p.full_name[0]}
                      </div>
                      <div>
                        <div className="text-xs font-bold text-slate-200 flex items-center gap-2">
                          <span>{p.full_name}</span>
                          {p.person_type === 'NEW' ? (
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/40">
                              NEW RECORD
                            </span>
                          ) : (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                              {p.person_id}
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          {p.district || 'Raipur'} • {p.occupation || 'Associate'} {p.phone_number ? `• ${p.phone_number}` : ''}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 self-end sm:self-auto">
                      <select
                        value={p.role}
                        onChange={e => handleUpdateRole(idx, e.target.value)}
                        className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs font-semibold text-slate-200 focus:outline-none"
                      >
                        {ROLES.map(r => (
                          <option key={r.value} value={r.value}>{r.label}</option>
                        ))}
                      </select>

                      <button
                        onClick={() => handleRemovePerson(idx)}
                        className="p-1.5 text-slate-500 hover:text-red-400 transition-colors"
                        title="Remove person"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Stepper buttons */}
            <div className="flex justify-between pt-4 border-t border-slate-800">
              <button
                onClick={() => setCurrentStep(1)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all cursor-pointer"
              >
                <ChevronLeft size={16} />
                <span>Back to Case Details</span>
              </button>

              <button
                disabled={associatedPersons.length === 0}
                onClick={() => setCurrentStep(3)}
                className={`flex items-center gap-1.5 px-5 py-2.5 rounded-xl text-xs font-bold transition-all shadow-lg ${
                  associatedPersons.length > 0
                    ? 'bg-indigo-600 hover:bg-indigo-500 text-white cursor-pointer'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                }`}
              >
                <span>Continue to Optional Entities</span>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ================= STEP 3: OPTIONAL ENTITIES ================= */}
      {currentStep === 3 && (
        <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 space-y-6 shadow-xl">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Building size={18} className="text-indigo-400" />
              Step 3 — Optional Structured Entities & Evidence Records
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Optionally record specific identifiers (Phone, Vehicle, Account) explicitly involved in the incident.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800">
            <div>
              <label className="text-xs font-semibold text-slate-300">Entity Type</label>
              <select
                value={entityInput.entity_type}
                onChange={e => setEntityInput({ ...entityInput, entity_type: e.target.value })}
                className="w-full mt-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-100"
              >
                <option value="PHONE">Phone Number</option>
                <option value="VEHICLE">Vehicle Registration</option>
                <option value="BANK_ACCOUNT">Bank Account</option>
              </select>
            </div>

            <div className="sm:col-span-2">
              <label className="text-xs font-semibold text-slate-300">Identifier Value</label>
              <div className="flex gap-2 mt-1">
                <input
                  type="text"
                  value={entityInput.value}
                  onChange={e => setEntityInput({ ...entityInput, value: e.target.value })}
                  placeholder={
                    entityInput.entity_type === 'PHONE' ? 'e.g. 9826012345' :
                    entityInput.entity_type === 'VEHICLE' ? 'e.g. CG 04 AB 1234' : 'e.g. 50100412345678'
                  }
                  className="flex-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
                <button
                  onClick={handleAddEntity}
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all cursor-pointer"
                >
                  Add
                </button>
              </div>
            </div>
          </div>

          {/* List of Added Optional Entities */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-slate-300">
              Attached Entities ({optionalEntities.length})
            </h3>
            {optionalEntities.length === 0 ? (
              <div className="text-xs text-slate-500 py-4 text-center bg-slate-950/40 rounded-xl border border-slate-800">
                No optional entities added. This step is entirely optional.
              </div>
            ) : (
              <div className="space-y-1.5">
                {optionalEntities.map((ent, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-800 text-slate-300">
                        {ent.entity_type}
                      </span>
                      <span className="font-semibold text-slate-200">{ent.value}</span>
                    </div>
                    <button
                      onClick={() => handleRemoveEntity(i)}
                      className="text-slate-500 hover:text-red-400"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-800">
            <button
              onClick={() => setCurrentStep(2)}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all cursor-pointer"
            >
              <ChevronLeft size={16} />
              <span>Back to People</span>
            </button>

            <button
              onClick={() => setCurrentStep(4)}
              className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg cursor-pointer"
            >
              <span>Continue to Review & Confirm</span>
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* ================= STEP 4: REVIEW & CONFIRM ================= */}
      {currentStep === 4 && (
        <div className="bg-slate-900/90 rounded-2xl border border-slate-800 p-6 space-y-6 shadow-xl">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <CheckCircle2 size={18} className="text-emerald-400" />
              Step 4 — Review & Commit Investigation Record
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Verify all entered parameters before committing to runtime isolated persistence.
            </p>
          </div>

          {/* Mandatory Non-Accusatory Safety Banner */}
          <div className="p-4 rounded-xl bg-amber-950/70 border border-amber-500/40 text-amber-200 text-xs space-y-1">
            <div className="font-bold flex items-center gap-2 text-amber-300">
              <ShieldAlert size={16} />
              <span>SYNTHETIC DEMONSTRATION DATA • INVESTIGATIVE INTEGRITY NOTICE</span>
            </div>
            <p className="text-[11px] text-amber-200/90">
              Case association indicates an analytical connection to an investigation record. It does <strong>NOT</strong> establish guilt, criminality, conviction, or culpability. All analytical information requires human verification.
            </p>
          </div>

          {/* Case Summary Card */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Case Details
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-950 text-indigo-300 border border-indigo-800/50">
                {caseData.status}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
              <div>
                <span className="text-slate-500 block text-[11px]">Title</span>
                <span className="font-semibold text-slate-100">{caseData.title}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[11px]">Offence Category</span>
                <span className="font-semibold text-slate-100">{caseData.offence_category}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[11px]">Incident Date</span>
                <span className="font-semibold text-slate-100">{caseData.incident_date}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[11px]">Police Station</span>
                <span className="font-semibold text-slate-100">{caseData.police_station}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[11px]">District & State</span>
                <span className="font-semibold text-slate-100">{caseData.district}, {caseData.state}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[11px]">FIR / Legal Section</span>
                <span className="font-semibold text-slate-100">
                  {caseData.fir_number || 'N/A'} • {caseData.legal_section || 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* People Summary */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
            <div className="text-xs font-bold text-slate-300 uppercase tracking-wider border-b border-slate-800 pb-2">
              Associated People ({associatedPersons.length})
            </div>
            <div className="space-y-2">
              {associatedPersons.map((p, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900 border border-slate-800/80 text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <User size={14} className="text-indigo-400" />
                    <span className="font-bold text-slate-200">{p.full_name}</span>
                    {p.person_type === 'NEW' ? (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/40 font-semibold">
                        NEW
                      </span>
                    ) : (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                        {p.person_id}
                      </span>
                    )}
                  </div>
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-950 text-indigo-300 border border-indigo-800/40">
                    {p.role}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Error display */}
          {saveError && (
            <div className="p-3 rounded-xl bg-red-950/80 border border-red-500/40 text-red-300 text-xs flex items-center gap-2">
              <AlertCircle size={16} className="shrink-0" />
              <span>{saveError}</span>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex justify-between pt-4 border-t border-slate-800">
            <button
              onClick={() => setCurrentStep(3)}
              disabled={saving}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all cursor-pointer"
            >
              <ChevronLeft size={16} />
              <span>Back to Edit</span>
            </button>

            <button
              onClick={handleFinalSave}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-xl cursor-pointer"
            >
              {saving ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Recording Case & Updating Graph…</span>
                </>
              ) : (
                <>
                  <CheckCircle2 size={16} />
                  <span>Save Investigation Record</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* ================= STEP 5: POST-SAVE CONFIRMATION ================= */}
      {currentStep === 5 && saveResult && (
        <div className="bg-slate-900/90 rounded-2xl border border-emerald-500/30 p-8 space-y-6 shadow-2xl text-center max-w-2xl mx-auto animate-fadeIn">
          <div className="w-16 h-16 rounded-2xl bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 mx-auto">
            <CheckCircle2 size={36} />
          </div>

          <div className="space-y-2">
            <h2 className="text-xl font-bold text-slate-100">
              Investigation Record Created Successfully
            </h2>
            <p className="text-xs text-slate-400">
              Allocated Case ID: <span className="font-mono font-bold text-indigo-400">{saveResult.case_id}</span> • Graph nodes and analytics updated
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-left space-y-2 text-xs">
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-400">Case Title:</span>
              <span className="font-bold text-slate-200">{saveResult.case_title}</span>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-400">Graph Entities Added:</span>
              <span className="font-bold text-emerald-400">+{saveResult.graph_summary?.nodes_added || 0} nodes</span>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-400">Graph Edges Added:</span>
              <span className="font-bold text-emerald-400">+{saveResult.graph_summary?.edges_added || 0} INVOLVED_IN edges</span>
            </div>
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">Persistence Status:</span>
              <span className="font-mono text-indigo-400">backend/data/runtime/</span>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <button
              onClick={() => navigate(`/cases/${saveResult.case_id}`)}
              className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-md cursor-pointer"
            >
              <FileText size={14} />
              <span>View Case Dossier</span>
            </button>

            <button
              onClick={() => navigate('/network')}
              className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition-all border border-slate-700 cursor-pointer"
            >
              <Network size={14} />
              <span>Open Network</span>
            </button>

            <button
              onClick={() => {
                // Reset form to register another case
                setCurrentStep(1);
                setCaseData({
                  title: '',
                  offence_category: 'Kidnapping',
                  incident_date: new Date().toISOString().split('T')[0],
                  police_station: 'Fictional PS No. 1, Raipur',
                  district: 'Raipur',
                  location: 'Raipur Market Area',
                  status: 'OPEN',
                  fir_number: '',
                  legal_section: 'IPC 363',
                  incident_time: '',
                  state: 'Chhattisgarh',
                  description: ''
                });
                setAssociatedPersons([]);
                setOptionalEntities([]);
                setSaveResult(null);
                api.get('/api/cases/next-id').then(res => setNextCaseId(res.data.next_case_id)).catch(() => {});
              }}
              className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition-all border border-slate-700 cursor-pointer"
            >
              <RotateCcw size={14} />
              <span>Register Another</span>
            </button>
          </div>
        </div>
      )}

      {/* ================= ADVISORY DUPLICATE WARNING MODAL ================= */}
      {duplicateModal.isOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-slate-900 border border-amber-500/50 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
                <AlertTriangle size={18} />
                <span>Advisory Duplicate / Possible Match Detected</span>
              </div>
              <button
                onClick={() => setDuplicateModal(prev => ({ ...prev, isOpen: false }))}
                className="text-slate-400 hover:text-slate-200"
              >
                <X size={16} />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              The entity resolution service detected matching registered records for <strong>{duplicateModal.pendingPersonData?.full_name}</strong>. Review these matches before creating a duplicate record:
            </p>

            <div className="space-y-2 max-h-52 overflow-y-auto">
              {duplicateModal.matches.map(m => (
                <div
                  key={m.person_id}
                  className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">{m.full_name}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      m.match_level === 'DUPLICATE' ? 'bg-red-950 text-red-300 border border-red-800/40' : 'bg-amber-950 text-amber-300 border border-amber-800/40'
                    }`}>
                      {m.match_level} ({Math.round(m.score * 100)}%)
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono">
                    ID: {m.person_id} • District: {m.district} • Phone: {m.phone_number || 'None'}
                  </div>
                  <div className="text-[11px] text-slate-400 italic">
                    Reason: {m.reason}
                  </div>

                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={() => {
                        // Link this existing person instead of creating a new one
                        handleLinkExistingPerson(m);
                        setDuplicateModal({ isOpen: false, checking: false, matches: [], pendingPersonData: null, pendingRole: 'PERSON_OF_INTEREST' });
                      }}
                      className="px-3 py-1 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 border border-indigo-500/40 text-xs font-semibold cursor-pointer"
                    >
                      Use This Existing Person ({m.person_id})
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-slate-800">
              <button
                onClick={() => setDuplicateModal(prev => ({ ...prev, isOpen: false }))}
                className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-300 text-xs font-medium cursor-pointer"
              >
                Cancel
              </button>

              <button
                onClick={() => {
                  // Explicit investigator decision: Create new person record anyway
                  commitAddNewPerson(duplicateModal.pendingPersonData, duplicateModal.pendingRole);
                }}
                className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold shadow-md cursor-pointer"
              >
                Create New Person Record Anyway
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
