import { useEffect, useState } from 'react';
import { Box, Toolbar } from '@mui/material';
import { Outlet } from 'react-router-dom';

import Sidebar from './Sidebar';
import TopBar, { type ApiStatus } from './TopBar';
import { checkHealth } from '../../api/client';

/**
 * Application shell: fixed top bar + collapsible dark sidebar + light content
 * area rendered via the router <Outlet />. Pings the backend health endpoint
 * on mount to drive the API status indicator.
 */
export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking');

  useEffect(() => {
    let active = true;
    checkHealth().then((ok) => {
      if (active) setApiStatus(ok ? 'connected' : 'disconnected');
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <TopBar
        onToggleSidebar={() => setCollapsed((c) => !c)}
        apiStatus={apiStatus}
      />
      <Sidebar collapsed={collapsed} />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: 'background.default',
          minHeight: '100vh',
          p: 3,
        }}
      >
        <Toolbar sx={{ minHeight: 56 }} />
        <Outlet />
      </Box>
    </Box>
  );
}
