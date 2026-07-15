import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Chip,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import RefreshIcon from '@mui/icons-material/Refresh';

import {
  listMigrationRuns,
  deleteMigrationRun,
  type MigrationRun,
} from '../api/migrations';
import { formatFileSize, formatDate } from '../utils/format';

const STATUS_COLORS: Record<string, 'default' | 'info' | 'warning' | 'success' | 'error'> = {
  created: 'default',
  uploading: 'info',
  validating: 'warning',
  migrating: 'info',
  completed: 'success',
  failed: 'error',
};

export default function MigrationRuns() {
  const navigate = useNavigate();
  const [runs, setRuns] = useState<MigrationRun[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchRuns = async () => {
    setLoading(true);
    setError('');
    try {
      const resp = await listMigrationRuns();
      setRuns(resp.runs);
      setTotal(resp.total);
    } catch {
      setError('Failed to load migration runs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const handleDelete = async (runId: number) => {
    try {
      await deleteMigrationRun(runId);
      setRuns((prev) => prev.filter((r) => r.id !== runId));
      setTotal((prev) => prev - 1);
    } catch {
      setError('Failed to delete migration run');
    }
  };

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Migration Runs
        </Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Tooltip title="Refresh">
            <IconButton onClick={fetchRuns}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/new-migration')}
          >
            New Migration
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!loading && runs.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary" gutterBottom>
            No migration runs yet.
          </Typography>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => navigate('/new-migration')}
          >
            Create Your First Migration
          </Button>
        </Paper>
      ) : (
        <TableContainer component={Paper} variant="outlined">
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Environment</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Files</TableCell>
                <TableCell align="right">Size</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {runs.map((run) => (
                <TableRow key={run.id} hover>
                  <TableCell>{run.id}</TableCell>
                  <TableCell>
                    <Typography sx={{ fontWeight: 500 }}>{run.name}</Typography>
                  </TableCell>
                  <TableCell>
                    <Chip label={run.environment} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={run.status}
                      size="small"
                      color={STATUS_COLORS[run.status] ?? 'default'}
                    />
                  </TableCell>
                  <TableCell align="right">{run.file_count}</TableCell>
                  <TableCell align="right">{formatFileSize(run.total_size)}</TableCell>
                  <TableCell>{formatDate(run.created_at)}</TableCell>
                  <TableCell align="center">
                    <Tooltip title="Delete run">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(run.id)}
                      >
                        <DeleteOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {total > 0 && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
          Showing {runs.length} of {total} migration runs
        </Typography>
      )}
    </Box>
  );
}
