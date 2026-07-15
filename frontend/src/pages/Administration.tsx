import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Paper,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import SecurityIcon from '@mui/icons-material/Security';
import TuneIcon from '@mui/icons-material/Tune';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

import { checkHealth } from '../api/client';

interface ConfigItem {
  key: string;
  label: string;
  value: string;
  description: string;
  editable: boolean;
}

const defaultConfigs: ConfigItem[] = [
  { key: 'max_upload_size', label: 'Max Upload Size (MB)', value: '100', description: 'Maximum file size per CSV upload', editable: true },
  { key: 'max_files_per_run', label: 'Max Files per Run', value: '50', description: 'Maximum number of files per migration run', editable: true },
  { key: 'staging_table_prefix', label: 'Staging Table Prefix', value: 'staging_', description: 'Prefix for auto-created staging tables', editable: true },
  { key: 'quality_pass_threshold', label: 'Quality Pass Threshold', value: '70', description: 'Minimum quality score (0-100) for PASS verdict', editable: true },
  { key: 'report_formats', label: 'Report Formats', value: 'json, html', description: 'Available report export formats', editable: false },
];

export default function Administration() {
  const [configs, setConfigs] = useState<ConfigItem[]>(defaultConfigs);
  const [dbStatus, setDbStatus] = useState<'unknown' | 'connected' | 'disconnected'>('unknown');
  const [checking, setChecking] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleCheckDb = async () => {
    setChecking(true);
    try {
      const healthy = await checkHealth();
      setDbStatus(healthy ? 'connected' : 'disconnected');
    } catch {
      setDbStatus('disconnected');
    } finally {
      setChecking(false);
    }
  };

  const handleConfigChange = (key: string, newValue: string) => {
    setConfigs((prev) =>
      prev.map((c) => (c.key === key ? { ...c, value: newValue } : c))
    );
    setSaved(false);
  };

  const handleSave = () => {
    // In production this would POST to /api/admin/config
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600 }} gutterBottom>
        Administration
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Manage platform configuration, database connections, and system settings.
      </Typography>

      <Stack spacing={3}>
        {/* Database Connection */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <StorageIcon color="primary" />
              <Typography variant="subtitle1">Database Connection</Typography>
            </Box>
            <Stack spacing={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 120 }}>
                  Status:
                </Typography>
                {dbStatus === 'unknown' ? (
                  <Chip label="Not checked" size="small" variant="outlined" />
                ) : dbStatus === 'connected' ? (
                  <Chip label="Connected" size="small" color="success" icon={<CheckCircleIcon />} />
                ) : (
                  <Chip label="Disconnected" size="small" color="error" />
                )}
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 120 }}>
                  Engine:
                </Typography>
                <Typography variant="body2">PostgreSQL 15</Typography>
              </Box>
              <Button
                variant="outlined"
                size="small"
                onClick={handleCheckDb}
                disabled={checking}
                sx={{ alignSelf: 'flex-start' }}
              >
                {checking ? 'Testing…' : 'Test Connection'}
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* Platform Configuration */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <TuneIcon color="primary" />
              <Typography variant="subtitle1">Platform Configuration</Typography>
            </Box>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Setting</TableCell>
                    <TableCell>Value</TableCell>
                    <TableCell>Description</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {configs.map((cfg) => (
                    <TableRow key={cfg.key}>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>{cfg.label}</Typography>
                      </TableCell>
                      <TableCell>
                        {cfg.editable ? (
                          <TextField
                            size="small"
                            value={cfg.value}
                            onChange={(e) => handleConfigChange(cfg.key, e.target.value)}
                            sx={{ width: 120 }}
                          />
                        ) : (
                          <Chip label={cfg.value} size="small" variant="outlined" />
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="text.secondary">{cfg.description}</Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
              <Button variant="contained" size="small" onClick={handleSave}>
                Save Configuration
              </Button>
              {saved && (
                <Alert severity="success" sx={{ py: 0 }}>
                  Configuration saved.
                </Alert>
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Security & Access */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <SecurityIcon color="primary" />
              <Typography variant="subtitle1">Security &amp; Access</Typography>
            </Box>
            <Stack spacing={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="body2">Authentication</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Require login to access the platform
                  </Typography>
                </Box>
                <Switch disabled defaultChecked={false} />
              </Box>
              <Divider />
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="body2">Role-Based Access Control</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Admin / Analyst / Viewer roles
                  </Typography>
                </Box>
                <Switch disabled defaultChecked={false} />
              </Box>
              <Divider />
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="body2">Audit Logging</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Track all user actions and data changes
                  </Typography>
                </Box>
                <Switch disabled defaultChecked={false} />
              </Box>
              <Alert severity="info" icon={<InfoOutlinedIcon />} sx={{ mt: 1 }}>
                Authentication, RBAC, and audit logging are planned for a future release.
              </Alert>
            </Stack>
          </CardContent>
        </Card>

        {/* System Info */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <InfoOutlinedIcon color="primary" />
              <Typography variant="subtitle1">System Information</Typography>
            </Box>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 500 }}>Platform</TableCell>
                    <TableCell>Migration Evaluation Platform (MEP)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 500 }}>Version</TableCell>
                    <TableCell>1.0.0</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 500 }}>Backend</TableCell>
                    <TableCell>FastAPI (Python 3.11)</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 500 }}>Frontend</TableCell>
                    <TableCell>React 19 + TypeScript + Material UI</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 500 }}>Database</TableCell>
                    <TableCell>PostgreSQL 15</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
