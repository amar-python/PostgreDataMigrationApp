import { AppBar, Box, IconButton, Toolbar, Tooltip, Typography } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';

type ApiStatus = 'checking' | 'connected' | 'disconnected';

interface TopBarProps {
  onToggleSidebar: () => void;
  apiStatus: ApiStatus;
}

const statusMeta: Record<ApiStatus, { color: string; label: string }> = {
  checking: { color: '#8A8886', label: 'Checking API…' },
  connected: { color: '#107C10', label: 'API Connected' },
  disconnected: { color: '#D13438', label: 'API Disconnected' },
};

/** Top app bar: menu toggle, product title, and live API status indicator. */
export default function TopBar({ onToggleSidebar, apiStatus }: TopBarProps) {
  const meta = statusMeta[apiStatus];

  return (
    <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
      <Toolbar sx={{ minHeight: 56 }}>
        <IconButton
          edge="start"
          aria-label="toggle navigation"
          onClick={onToggleSidebar}
          sx={{ mr: 2, color: 'text.primary' }}
        >
          <MenuIcon />
        </IconButton>

        <Typography variant="h6" sx={{ flexGrow: 1, fontSize: 16 }}>
          Migration Evaluation Platform
        </Typography>

        <Tooltip title={meta.label}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
            <FiberManualRecordIcon
              sx={{
                fontSize: 12,
                color: meta.color,
                animation:
                  apiStatus === 'checking' ? 'pulse 1.2s ease-in-out infinite' : 'none',
                '@keyframes pulse': {
                  '0%, 100%': { opacity: 1 },
                  '50%': { opacity: 0.3 },
                },
              }}
            />
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {meta.label}
            </Typography>
          </Box>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
}

export type { ApiStatus };
