import { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import StorageIcon from '@mui/icons-material/Storage';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import TableRowsIcon from '@mui/icons-material/TableRows';
import PlaylistAddCheckIcon from '@mui/icons-material/PlaylistAddCheck';

import { getDashboardStats, type DashboardStats } from '../api/validation';
import { formatFileSize, formatDate } from '../utils/format';

const statusColor = (s: string): 'default' | 'primary' | 'success' | 'error' | 'warning' | 'info' => {
  switch (s) {
    case 'completed': return 'success';
    case 'ready': return 'primary';
    case 'failed':
    case 'error': return 'error';
    case 'migrating':
    case 'validating': return 'warning';
    case 'uploading': return 'info';
    default: return 'default';
  }
};

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  return (
    <Card sx={{ flex: 1, minWidth: 160 }}>
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 2, '&:last-child': { pb: 2 } }}>
        <Box sx={{ bgcolor: color, borderRadius: 2, p: 1.5, display: 'flex', color: '#fff' }}>
          {icon}
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary">{title}</Typography>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>{value}</Typography>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <Typography color="text.secondary">Loading dashboard…</Typography>
      </Box>
    );
  }

  if (!stats) {
    return (
      <Box sx={{ textAlign: 'center', mt: 8 }}>
        <DashboardIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
        <Typography color="text.secondary">Unable to load dashboard data.</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600 }} gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Overview of all migration runs, files, and data quality.
      </Typography>

      {/* Stat cards */}
      <Stack direction="row" spacing={2} sx={{ mb: 4, flexWrap: 'wrap' }}>
        <StatCard title="Total Runs" value={stats.total_runs} icon={<PlaylistAddCheckIcon />} color="#0078D4" />
        <StatCard title="Total Files" value={stats.total_files} icon={<InsertDriveFileIcon />} color="#5C2D91" />
        <StatCard title="Total Rows" value={stats.total_rows.toLocaleString()} icon={<TableRowsIcon />} color="#107C10" />
        <StatCard title="Total Size" value={formatFileSize(stats.total_size)} icon={<StorageIcon />} color="#D83B01" />
      </Stack>

      {/* Status breakdown */}
      {Object.keys(stats.runs_by_status).length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>Runs by Status</Typography>
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
              {Object.entries(stats.runs_by_status).map(([status, count]) => (
                <Chip
                  key={status}
                  label={`${status}: ${count}`}
                  color={statusColor(status)}
                  variant="outlined"
                />
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* Recent runs table */}
      <Typography variant="subtitle1" gutterBottom>Recent Migration Runs</Typography>
      {stats.recent_runs.length === 0 ? (
        <Paper variant="outlined" sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">
            No migration runs yet. Go to <strong>New Migration</strong> to get started.
          </Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Environment</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Files</TableCell>
                <TableCell align="right">Size</TableCell>
                <TableCell>Created</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {stats.recent_runs.map((run) => (
                <TableRow key={run.id} hover>
                  <TableCell>{run.id}</TableCell>
                  <TableCell><Typography sx={{ fontWeight: 500 }}>{run.name}</Typography></TableCell>
                  <TableCell>
                    <Chip label={run.environment} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <Chip label={run.status} size="small" color={statusColor(run.status)} />
                  </TableCell>
                  <TableCell align="right">{run.file_count}</TableCell>
                  <TableCell align="right">{formatFileSize(run.total_size)}</TableCell>
                  <TableCell>{formatDate(run.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
