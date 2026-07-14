import { Navigate, Route, Routes } from 'react-router-dom';

import AppLayout from './components/Layout/AppLayout';
import Dashboard from './pages/Dashboard';
import MigrationRuns from './pages/MigrationRuns';
import NewMigration from './pages/NewMigration';
import Validation from './pages/Validation';
import Reports from './pages/Reports';
import History from './pages/History';
import Administration from './pages/Administration';

/** Top-level routing: all pages render inside the shared AppLayout shell. */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="migration-runs" element={<MigrationRuns />} />
        <Route path="new-migration" element={<NewMigration />} />
        <Route path="validation" element={<Validation />} />
        <Route path="reports" element={<Reports />} />
        <Route path="history" element={<History />} />
        <Route path="administration" element={<Administration />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
