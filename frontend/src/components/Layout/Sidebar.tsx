import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import HubIcon from '@mui/icons-material/Hub';
import { useLocation, useNavigate } from 'react-router-dom';

import { navItems } from './navConfig';

const EXPANDED_WIDTH = 240;
const COLLAPSED_WIDTH = 64;

interface SidebarProps {
  collapsed: boolean;
}

/**
 * Dark navigation drawer, Azure-Portal style. Highlights the active route and
 * collapses to an icon-only rail when `collapsed` is true.
 */
export default function Sidebar({ collapsed }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const width = collapsed ? COLLAPSED_WIDTH : EXPANDED_WIDTH;

  const isActive = (path: string) =>
    path === '/'
      ? location.pathname === '/'
      : location.pathname.startsWith(path);

  return (
    <Drawer
      variant="permanent"
      sx={{
        width,
        flexShrink: 0,
        whiteSpace: 'nowrap',
        '& .MuiDrawer-paper': {
          width,
          boxSizing: 'border-box',
          backgroundColor: '#1B1A19',
          color: '#F3F2F1',
          borderRight: 'none',
          overflowX: 'hidden',
          transition: 'width 0.2s ease',
        },
      }}
    >
      <Toolbar
        sx={{
          minHeight: 56,
          px: collapsed ? 1.5 : 2,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <HubIcon sx={{ color: '#2B88D8' }} />
        {!collapsed && (
          <Typography variant="subtitle1" noWrap sx={{ color: '#FFFFFF' }}>
            MEP
          </Typography>
        )}
      </Toolbar>

      <Box sx={{ overflow: 'hidden', mt: 1 }}>
        <List>
          {navItems.map((item) => {
            const active = isActive(item.path);
            return (
              <ListItem key={item.path} disablePadding sx={{ display: 'block' }}>
                <Tooltip
                  title={collapsed ? item.label : ''}
                  placement="right"
                  arrow
                >
                  <ListItemButton
                    selected={active}
                    onClick={() => navigate(item.path)}
                    sx={{
                      minHeight: 44,
                      justifyContent: collapsed ? 'center' : 'initial',
                      px: 2.5,
                      color: active ? '#FFFFFF' : '#C8C6C4',
                      borderLeft: active
                        ? '3px solid #2B88D8'
                        : '3px solid transparent',
                      '&.Mui-selected': {
                        backgroundColor: 'rgba(43,136,216,0.16)',
                      },
                      '&.Mui-selected:hover': {
                        backgroundColor: 'rgba(43,136,216,0.24)',
                      },
                      '&:hover': {
                        backgroundColor: 'rgba(255,255,255,0.06)',
                      },
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: 0,
                        mr: collapsed ? 0 : 2,
                        justifyContent: 'center',
                        color: active ? '#2B88D8' : '#C8C6C4',
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    {!collapsed && (
                      <ListItemText
                        primary={item.label}
                        slotProps={{
                          primary: {
                            sx: {
                              fontSize: 14,
                              fontWeight: active ? 600 : 400,
                            },
                          },
                        }}
                      />
                    )}
                  </ListItemButton>
                </Tooltip>
              </ListItem>
            );
          })}
        </List>
      </Box>
    </Drawer>
  );
}

export { EXPANDED_WIDTH, COLLAPSED_WIDTH };
