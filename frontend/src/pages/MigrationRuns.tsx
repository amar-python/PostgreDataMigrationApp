import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  Paper,
  Stack,
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
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AssessmentIcon from '@mui/icons-material/Assessment';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

import {
  listMigrationRuns,
  deleteMigrationRun,
  type MigrationRun,
} from '../api/migrations';
import { executeMigration, evaluateRun, type ExecutionResponse, type EvaluationResponse } from '../api/validation';
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
  const [actionRunId, setActionRunId] = useState<number | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Result dialog
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogTitle, setDialogTitle] = useState('');
  const [dialogResult, setDialogResult] = useState<ExecutionResponse | EvaluationResponse | null>(null);

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

  useEffect(() => { fetchRuns(); }, []);

  const handleDelete = async (runId: number) => {
    try {
      await deleteMigrationRun(runId);
      setRuns((prev) => prev.filter((r) => r.id !== runId));
      setTotal((prev) => prev - 1);
    } catch {
      setError('Failed to delete migration run');
    }
  };

  const handleExecute = async (runId: number) => {
    setActionRunId(runId);
    setActionLoading(true);
    setError('');
    try {
      const res = await executeMigration(runId);
      setDialogTitle('Migration Result');
      setDialogResult(res);
      setDialogOpen(true);
      fetchRuns(); // refresh statuses
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Migration execution failed');
    } finally {
      setActionLoading(false);
      setActionRunId(null);
    }
  };

  const handleEvaluate = async (runId: number) => {
    setActionRunId(runId);
    setActionLoading(true);
    setError('');
    try {
      const res = await evaluateRun(runId);
      setDialogTitle('Evaluation Result');
      setDialogResult(res);
      setDialogOpen(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Evaluation failed');
    } finally {
      setActionLoading(false);
      setActionRunId(null);
    }
  };

  const renderResultDialog = () => {
    if (!dialogResult) return null;
    const summary = dialogResult.summary as any;
    const isEval = 'overall_score' in summary;

    return (
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{dialogTitle}</DialogTitle>
        <DialogContent>
          {isEval ? (
            <Stack spacing={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {summary.verdict === 'PASS'
                  ? <CheckCircleIcon color="success" sx={{ fontSize: 40 }} />
                  : <ErrorIcon color="error" sx={{ fontSize: 40 }} />}
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700 }}>{summary.overall_score}/100</Typography>
                  <Chip label={summary.verdict} color={summary.verdict === 'PASS' ? 'success' : 'error'} />
                </Box>
              </Box>
              <Typography variant="body2">
                Source rows: {summary.total_source_rows?.toLocaleString()} →
                Target rows: {summary.total_target_rows?.toLocaleString()}
              </Typography>
              {dialogResult.files.map((f: any) => (
                <Paper key={f.file_id} variant="outlined" sx={{ p: 1.5 }}>
                  <Typography sx={{ fontWeight: 500 }}>{f.filename}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Score: {f.score}/100 — {f.source_rows} → {f.target_rows} rows
                  </Typography>
                </Paper>
              ))}
            </Stack>
          ) : (
            <Stack spacing={2}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {summary.success
                  ? <CheckCircleIcon color="success" sx={{ fontSize: 40 }} />
                  : <ErrorIcon color="error" sx={{ fontSize: 40 }} />}
                <Box>
                  <Typography variant="h6">
                    {summary.tables_created} table(s) created, {summary.total_rows_loaded?.toLocaleString()} rows loaded
                  </Typography>
                </Box>
              </Box>
              {dialogResult.files.map((f: any) => (
                <Paper key={f.file_id} variant="outlined" sx={{ p: 1.5 }}>
                  <Typography sx={{ fontWeight: 500 }}>{f.filename}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Table: {f.table_name || '—'} — {f.rows_loaded?.toLocaleString()} rows — {f.status}
                  </Typography>
                  {f.error && <Typography variant="body2" color="error.main">{f.error}</Typography>}
                </Paper>
              ))}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  };

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>Migration Runs</Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Tooltip title="Refresh">
            <IconButton onClick={fetchRuns}><RefreshIcon /></IconButton>
          </Tooltip>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => navigate('/new-migration')}>
            New Migration
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {actionLoading && <LinearProgress sx={{ mb: 1 }} />}

      {!loading && runs.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary" gutterBottom>No migration runs yet.</Typography>
          <Button variant="outlined" startIcon={<AddIcon />} onClick={() => navigate('/new-migration')}>
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
                  <TableCell><Typography sx={{ fontWeight: 500 }}>{run.name}</Typography></TableCell>
                  <TableCell><Chip label={run.environment} size="small" variant="outlined" /></TableCell>
                  <TableCell>
                    <Chip label={run.status} size="small" color={STATUS_COLORS[run.status] ?? 'default'} />
                  </TableCell>
                  <TableCell align="right">{run.file_count}</TableCell>
                  <TableCell align="right">{formatFileSize(run.total_size)}</TableCell>
                  <TableCell>{formatDate(run.created_at)}</TableCell>
                  <TableCell align="center">
                    <Stack direction="row" spacing={0.5} sx={{ justifyContent: 'center' }}>
                      <Tooltip title="Execute migration">
                        <IconButton
                          size="small"
                          color="primary"
                          disabled={actionLoading && actionRunId === run.id}
                          onClick={() => handleExecute(run.id)}
                        >
                          {actionLoading && actionRunId === run.id
                            ? <CircularProgress size={16} />
                            : <PlayArrowIcon fontSize="small" />}
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Evaluate quality">
                        <IconButton
                          size="small"
                          color="success"
                          disabled={actionLoading}
                          onClick={() => handleEvaluate(run.id)}
                        >
                          <AssessmentIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete run">
                        <IconButton size="small" color="error" onClick={() => handleDelete(run.id)}>
                          <DeleteOutlinedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Stack>
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

      {renderResultDialog()}
    </Box>
  );
}
