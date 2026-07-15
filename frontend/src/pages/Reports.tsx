import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import DownloadIcon from '@mui/icons-material/Download';
import CodeIcon from '@mui/icons-material/Code';
import HtmlIcon from '@mui/icons-material/Html';

import { listMigrationRuns, type MigrationRun } from '../api/migrations';
import { generateReport } from '../api/validation';

export default function Reports() {
  const [runs, setRuns] = useState<MigrationRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | ''>('');
  const [format, setFormat] = useState<'json' | 'html'>('html');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ format: string; download_url: string } | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    listMigrationRuns().then((r) => setRuns(r.runs)).catch(() => {});
  }, []);

  const handleGenerate = async () => {
    if (!selectedRunId) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await generateReport(selectedRunId, format);
      setResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Report generation failed');
    } finally {
      setLoading(false);
    }
  };

  const downloadUrl = result
    ? `${import.meta.env.VITE_API_BASE_URL ?? '/api'}${result.download_url.replace('/api', '')}`
    : '';

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600 }} gutterBottom>
        Reports
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Generate and download migration reports in JSON or HTML format.
      </Typography>

      <Card sx={{ maxWidth: 600, mb: 3 }}>
        <CardContent>
          <Stack spacing={2}>
            <TextField
              select
              label="Migration Run"
              value={selectedRunId}
              onChange={(e) => { setSelectedRunId(Number(e.target.value)); setResult(null); }}
              fullWidth
              size="small"
            >
              {runs.map((r) => (
                <MenuItem key={r.id} value={r.id}>
                  {r.name} — {r.status}
                </MenuItem>
              ))}
            </TextField>

            <TextField
              select
              label="Report Format"
              value={format}
              onChange={(e) => { setFormat(e.target.value as 'json' | 'html'); setResult(null); }}
              fullWidth
              size="small"
            >
              <MenuItem value="html">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <HtmlIcon fontSize="small" /> HTML Report
                </Box>
              </MenuItem>
              <MenuItem value="json">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CodeIcon fontSize="small" /> JSON Report
                </Box>
              </MenuItem>
            </TextField>

            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <DescriptionIcon />}
              disabled={!selectedRunId || loading}
              onClick={handleGenerate}
            >
              {loading ? 'Generating…' : 'Generate Report'}
            </Button>
          </Stack>
        </CardContent>
      </Card>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Alert
          severity="success"
          action={
            <Button
              color="inherit"
              size="small"
              startIcon={<DownloadIcon />}
              href={downloadUrl}
              target="_blank"
              rel="noopener"
            >
              Download
            </Button>
          }
        >
          {result.format.toUpperCase()} report generated successfully.
        </Alert>
      )}
    </Box>
  );
}
