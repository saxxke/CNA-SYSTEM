import React from 'react';
import { Phone, CreditCard, Car, Building2, MapPin, Database, Shield } from 'lucide-react';

export default function PersonAssets({ assets = {} }) {
  const phones = assets.phones || [];
  const bankAccounts = assets.bank_accounts || [];
  const vehicles = assets.vehicles || [];
  const organization = assets.organization;
  const location = assets.location;

  const totalAssets = (assets.total_assets_count ?? (
    phones.length + bankAccounts.length + vehicles.length + (organization ? 1 : 0) + (location ? 1 : 0)
  ));

  return (
    <div className="space-y-6 select-none">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database size={16} className="text-indigo-400" />
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Linked Assets & Identifiers</h2>
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
            {totalAssets} Indexed
          </span>
        </div>
        <p className="text-xs text-slate-400 hidden sm:block">
          Official assets, financial accounts, and registered telecom identifiers.
        </p>
      </div>

      {totalAssets === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-slate-950/80 rounded-xl border border-slate-800 text-xs">
          No external assets (phones, vehicles, bank accounts) registered for this person record.
        </div>
      ) : (
        <div className="space-y-5">
          {/* Registered Phones */}
          {phones.length > 0 && (
            <div className="space-y-2.5">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Phone size={13} className="text-emerald-400" />
                Registered Telecom Identifiers ({phones.length})
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {phones.map((ph, idx) => (
                  <div key={`${ph.phone_id}-${idx}`} className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl shadow-xs flex items-start gap-3">
                    <div className="p-2 bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-lg shrink-0 mt-0.5">
                      <Phone size={14} />
                    </div>
                    <div className="text-xs space-y-0.5 overflow-hidden">
                      <div className="font-mono font-bold text-slate-100 text-sm">{ph.phone_number}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{ph.phone_id} • {ph.phone_type}</div>
                      <div className="text-[10px] text-slate-400">{ph.carrier}</div>
                      {ph.is_primary && (
                        <span className="inline-block mt-1 text-[10px] text-emerald-300 bg-emerald-950/80 px-2 py-0.5 rounded font-medium border border-emerald-800">
                          Primary Device
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Registered Bank Accounts */}
          {bankAccounts.length > 0 && (
            <div className="space-y-2.5">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <CreditCard size={13} className="text-amber-400" />
                Financial Instruments & Accounts ({bankAccounts.length})
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {bankAccounts.map((b, idx) => (
                  <div key={`${b.account_id}-${idx}`} className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl shadow-xs flex items-start gap-3">
                    <div className="p-2 bg-amber-950 text-amber-400 border border-amber-800 rounded-lg shrink-0 mt-0.5">
                      <CreditCard size={14} />
                    </div>
                    <div className="text-xs space-y-0.5 overflow-hidden">
                      <div className="font-mono font-bold text-slate-100">{b.account_number}</div>
                      <div className="text-[11px] text-slate-300 font-medium">{b.bank_name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{b.account_id} • {b.branch || 'Main Branch'}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Registered Vehicles */}
          {vehicles.length > 0 && (
            <div className="space-y-2.5">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Car size={13} className="text-purple-400" />
                Registered Transport & Vehicles ({vehicles.length})
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {vehicles.map((v, idx) => (
                  <div key={`${v.vehicle_id}-${idx}`} className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl shadow-xs flex items-start gap-3">
                    <div className="p-2 bg-purple-950 text-purple-400 border border-purple-800 rounded-lg shrink-0 mt-0.5">
                      <Car size={14} />
                    </div>
                    <div className="text-xs space-y-0.5 overflow-hidden">
                      <div className="font-mono font-bold text-slate-100">{v.registration_number}</div>
                      <div className="text-[11px] text-slate-300 font-medium">{v.model || 'Vehicle'} • {v.vehicle_type}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{v.vehicle_id}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Organization & Location */}
          {(organization || location) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              {organization && (
                <div className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl flex items-start gap-3">
                  <div className="p-2 bg-pink-950 text-pink-400 border border-pink-800 rounded-lg shrink-0">
                    <Building2 size={14} />
                  </div>
                  <div className="text-xs space-y-0.5">
                    <div className="text-[10px] uppercase font-bold text-slate-400">Associated Business</div>
                    <div className="font-bold text-slate-100">{organization.org_name || organization.name}</div>
                    <div className="text-[10px] text-slate-400 font-mono">{organization.org_id}</div>
                  </div>
                </div>
              )}

              {location && (
                <div className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl flex items-start gap-3">
                  <div className="p-2 bg-red-950 text-red-400 border border-red-800 rounded-lg shrink-0">
                    <MapPin size={14} />
                  </div>
                  <div className="text-xs space-y-0.5">
                    <div className="text-[10px] uppercase font-bold text-slate-400">Registered Address</div>
                    <div className="font-bold text-slate-100">{location.address || location.locality}</div>
                    <div className="text-[10px] text-slate-400 font-mono">{location.location_id} • {location.district}</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
