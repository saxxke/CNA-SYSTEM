import React from 'react';
import AuditLogViewer from '../components/audit/AuditLogViewer';

export default function AuditLogsPage() {
  return (
    <div className="p-6 max-w-7xl mx-auto select-none animate-fadeIn">
      <AuditLogViewer />
    </div>
  );
}
