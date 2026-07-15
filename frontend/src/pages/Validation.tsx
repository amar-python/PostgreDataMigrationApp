import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Collapse,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';

import { listMigrationRuns, type MigrationRun } from '../api/migrations';
import {
  validateRun,
  type ValidationResponse,
  type FileValidationResult,
} from '../api/validation';

const severityIcon = (s: string) => {
  switch (s) {
    case 'error': return <ErrorIcon fontSize="small" color="error" />;
    case 'warning': return <WarningIcon fontSize="small" sx={{ color: '#FFB900' }} />;
    default: return <InfoIcon fontSize="small" color="info" />;
  }
};

const typeChip = (t: string) => {
  const colors: Record<string, 'primary' | 'secondary' | 'success' | 'warning' | 'info'> = {
    integer: 'primary', decimal: 'secondary', date: 'warning',
    boolean: 'success', text: 'info',
  };
  return <Chip label={t} size="small" color={colors[t] || 'default'} variant="outlined" />;
};

export default function Validation() {
  const [runs, setRuns] = useState<MigrationRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | ''>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ValidationResponse | null>(null);
  const [error, setError] = useState('');
  const [expandedFile, setExpandedFile] = useState<number | null>(null);

  useEffect(() => {
    listMigrationRuns().then((r) => setRuns(r.runs)).catch(() => {});
  }, []);

  const handleValidate = async () => {
    if (!selectedRunId) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await validateRun(selectedRunId);
      setResult(res);
      if (res.files.length > 0) setExpandedFile(res.files[0].file_id);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Validation failed');
    } finally {
      setLoading(false);
    }
  };

  const renderSummary = () => {
    if (!result) return null;
    const { summary } = result;
    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            {summary.passed
              ? <CheckCircleIcon color="success" sx={{ fontSize: 32 }} />
              : <ErrorIcon color="error" sx={{ fontSize: 32 }} />}
            <Typography variant="h6">
              {summary.passed ? 'All Checks Passed' : 'Validation Issues Found'}
            </Typography>
          </Box>
          <Stack direction="row" spacing={4} sx={{ mt: 1 }}>
            <Box>
              <Typography variant="caption" color="text.secondary">Files</Typography>
              <Typography variant="h5">{summary.total_files}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Errors</Typography>
              <Typography variant="h5" color="error.main">{summary.errors}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Warnings</Typography>
              <Typography variant="h5" sx={{ color: '#FFB900' }}>{summary.warnings}</Typography>
            </Box>
          </Stack>
        </CardContent>
      </Card>
    );
  };

  const renderFileResult = (fr: FileValidationResult) => {
    const isExpanded = expandedFile === fr.file_id;
    const errors = fr.issues.filter((i) => i.severity === 'error').length;
    const warnings = fr.issues.filter((i) => i.severity === 'warning').length;
    const statusColor = errors > 0 ? 'error' : warnings > 0 ? 'warning' : 'success';

    return (
      <Paper key={fr.file_id} variant="outlined" sx={{ mb: 2 }}>
        <Box
          sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
          onClick={() => setExpandedFile(isExpanded ? null : fr.file_id)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FactCheckIcon color={statusColor as any} />
            <Typography sx={{ fontWeight: 600 }}>{fr.filename}</Typography>
            <Chip label={`${fr.schema.length} cols`} size="small" variant="outlined" />
            {errors > 0 && <Chip label={`${errors} errors`} size="small" color="error" />}
            {warnings > 0 && <Chip label={`${warnings} warnings`} size="small" sx={{ bgcolor: '#FFF3CD', color: '#856404' }} />}
          </Box>
          <IconButton size="small">{isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}</IconButton>
        </Box>

        <Collapse in={isExpanded}>
          <Box sx={{ px: 2, pb: 2 }}>
            {/* Schema table */}
            <Typography variant="subtitle2" sx={{ mt: 1, mb: 1 }}>Inferred Schema</Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Column</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell align="center">Nullable</TableCell>
                    <TableCell align="center">Unique</TableCell>
                    <TableCell align="right">Nulls</TableCell>
                    <TableCell>Samples</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {fr.schema.map((col) => (
                    <TableRow key={col.name}>
                      <TableCell><Typography variant="body2" sx={{ fontWeight: 500 }}>{col.name}</Typography></TableCell>
                      <TableCell>{typeChip(col.inferred_type)}</TableCell>
                      <TableCell align="center">{col.nullable ? '✓' : '—'}</TableCell>
                      <TableCell align="center">{col.unique ? '✓' : '—'}</TableCell>
                      <TableCell align="right">{col.null_count} / {col.total_count}</TableCell>
                      <TableCell>
                        <Typography variant="caption" color="text.secondary" sx={{ maxWidth: 200, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {col.sample_values.join(', ')}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {/* Issues */}
            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>Validation Issues ({fr.issues.length})</Typography>
            <Stack spacing={0.5}>
              {fr.issues.map((issue, idx) => (
                <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 0.5 }}>
                  {severityIcon(issue.severity)}
                  {issue.column && <Chip label={issue.column} size="small" variant="outlined" />}
                  <Typography variant="body2">{issue.message}</Typography>
                </Box>
              ))}
            </Stack>
          </Box>
        </Collapse>
      </Paper>
    );
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600 }} gutterBottom>
        Schema Discovery &amp; Validation
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Select a migration run to discover column schemas and run data-quality checks.
      </Typography>

      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <TextField
          select
          label="Migration Run"
          value={selectedRunId}
          onChange={(e) => setSelectedRunId(Number(e.target.value))}
          sx={{ minWidth: 300 }}
          size="small"
        >
          {runs.map((r) => (
            <MenuItem key={r.id} value={r.id}>
              {r.name} ({r.file_count} files) — {r.status}
            </MenuItem>
          ))}
        </TextField>
        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <PlayArrowIcon />}
          disabled={!selectedRunId || loading}
          onClick={handleValidate}
        >
          {loading ? 'Validating…' : 'Run Validation'}
        </Button>
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <>
          {renderSummary()}
          {result.files.map(renderFileResult)}
        </>
      )}
    </Box>
  );
}
