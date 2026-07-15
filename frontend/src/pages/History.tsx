import { useEffect, useState } from 'react';
import {
  Box,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';

import { listMigrationRuns, type MigrationRun } from '../api/migrations';
import { formatFileSize, formatDate } from '../utils/format';

const STATUS_COLORS: Record<string, 'default' | 'info' | 'warning' | 'success' | 'error'> = {
  created: 'default',
  uploading: 'info',
  validating: 'warning',
  migrating: 'info',
  completed: 'success',
  failed: 'error',
};

export default function History() {
  const [runs, setRuns] = useState<MigrationRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listMigrationRuns()
      .then((r) => setRuns(r.runs))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <Typography color="text.secondary">Loading history…</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600 }} gutterBottom>
        Migration History
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Complete chronological log of all migration runs.
      </Typography>

      {runs.length === 0 ? (
        <Paper variant="outlined" sx={{ p: 4, textAlign: 'center' }}>
          <HistoryIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
          <Typography color="text.secondary">No migration history yet.</Typography>
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
                <TableCell>Updated</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {runs.map((run) => (
                <TableRow key={run.id} hover>
                  <TableCell>{run.id}</TableCell>
                  <TableCell><Typography sx={{ fontWeight: 500 }}>{run.name}</Typography></TableCell>
                  <TableCell><Chip label={run.environment} size="small" variant="outlined" /></TableCell>
                  <TableCell>
                    <Chip label={run.status} size="small" color={STATUS_COLORS[run.status] ?? 'default'} />
                  </TableCell>
                  <TableCell align="right">{run.file_count}</TableCell>
                  <TableCell align="right">{formatFileSize(run.total_size)}</TableCell>
                  <TableCell>{formatDate(run.created_at)}</TableCell>
                  <TableCell>{formatDate(run.updated_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
