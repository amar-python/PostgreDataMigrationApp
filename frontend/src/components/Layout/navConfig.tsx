import type { ReactNode } from 'react';
import DashboardIcon from '@mui/icons-material/Dashboard';
import StorageIcon from '@mui/icons-material/Storage';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutlineOutlined';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import AssessmentIcon from '@mui/icons-material/Assessment';
import HistoryIcon from '@mui/icons-material/History';
import SettingsIcon from '@mui/icons-material/Settings';

export interface NavItem {
  label: string;
  path: string;
  icon: ReactNode;
}

/** Sidebar navigation items, in display order. */
export const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: <DashboardIcon /> },
  { label: 'Migration Runs', path: '/migration-runs', icon: <StorageIcon /> },
  { label: 'New Migration', path: '/new-migration', icon: <AddCircleOutlineIcon /> },
  { label: 'Validation', path: '/validation', icon: <FactCheckIcon /> },
  { label: 'Reports', path: '/reports', icon: <AssessmentIcon /> },
  { label: 'History', path: '/history', icon: <HistoryIcon /> },
  { label: 'Administration', path: '/administration', icon: <SettingsIcon /> },
];
