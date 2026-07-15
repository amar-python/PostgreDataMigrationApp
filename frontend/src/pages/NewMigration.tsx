import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  LinearProgress,
  Paper,
  Stack,
  Step,
  StepLabel,
  Stepper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  MenuItem,
  Typography,
  Tooltip,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import CheckCircleOutlinedIcon from '@mui/icons-material/CheckCircleOutlined';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';

import {
  createMigrationRun,
  uploadFiles,
  listFiles,
  deleteFile as apiDeleteFile,
  type MigrationRun,
  type UploadedFile,
} from '../api/migrations';
import { formatFileSize, formatDate } from '../utils/format';

const ENVIRONMENTS = ['development', 'staging', 'production'];
const STEPS = ['Configure', 'Upload Files', 'Summary'];

export default function NewMigration() {
  // --- Stepper ---
  const [activeStep, setActiveStep] = useState(0);

  // --- Step 1: Configure ---
  const [name, setName] = useState('');
  const [environment, setEnvironment] = useState('development');
  const [description, setDescription] = useState('');
  const [run, setRun] = useState<MigrationRun | null>(null);
  const [createError, setCreateError] = useState('');

  // --- Step 2: Upload ---
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // --- Step 1 handlers ---
  const handleCreateRun = async () => {
    if (!name.trim()) return;
    setCreateError('');
    try {
      const created = await createMigrationRun({
        name: name.trim(),
        environment,
        description: description.trim() || undefined,
      });
      setRun(created);
      setActiveStep(1);
    } catch (err: any) {
      setCreateError(err?.response?.data?.detail || 'Failed to create migration run');
    }
  };

  // --- Step 2 handlers ---
  const addFiles = (incoming: FileList | File[]) => {
    const arr = Array.from(incoming);
    // Avoid duplicate filenames in the pending list
    setPendingFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name));
      const novel = arr.filter((f) => !existing.has(f.name));
      return [...prev, ...novel];
    });
  };

  const removePendingFile = (name: string) => {
    setPendingFiles((prev) => prev.filter((f) => f.name !== name));
  };

  const handleUpload = async () => {
    if (!run || pendingFiles.length === 0) return;
    setUploadError('');
    setUploading(true);
    setUploadProgress(0);
    try {
      const results = await uploadFiles(run.id, pendingFiles, setUploadProgress);
      setUploadedFiles((prev) => [...prev, ...results]);
      setPendingFiles([]);
    } catch (err: any) {
      setUploadError(err?.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteFile = async (fileId: number) => {
    try {
      await apiDeleteFile(fileId);
      setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
    } catch {
      // Silently fail — user can retry
    }
  };

  // Refresh uploaded file list when entering step 2
  useEffect(() => {
    if (run && activeStep === 1) {
      listFiles(run.id).then((resp) => setUploadedFiles(resp.files)).catch(() => {});
    }
  }, [run, activeStep]);

  // --- Drag-and-drop handlers ---
  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);
  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
  }, []);

  // ---------------------------------------------------------------------------
  // Render helpers
  // ---------------------------------------------------------------------------

  const renderConfigureStep = () => (
    <Card sx={{ maxWidth: 600, mx: 'auto', mt: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Migration Details
        </Typography>
        <Stack spacing={3} sx={{ mt: 1 }}>
          <TextField
            label="Migration Name"
            required
            fullWidth
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Q3 Customer Migration"
          />
          <TextField
            label="Environment"
            select
            fullWidth
            value={environment}
            onChange={(e) => setEnvironment(e.target.value)}
          >
            {ENVIRONMENTS.map((env) => (
              <MenuItem key={env} value={env}>
                {env.charAt(0).toUpperCase() + env.slice(1)}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Description (optional)"
            fullWidth
            multiline
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the purpose of this migration..."
          />
          {createError && <Alert severity="error">{createError}</Alert>}
          <Button
            variant="contained"
            size="large"
            disabled={!name.trim()}
            onClick={handleCreateRun}
          >
            Create &amp; Continue
          </Button>
        </Stack>
      </CardContent>
    </Card>
  );

  const renderUploadStep = () => (
    <Box sx={{ mt: 2 }}>
      {/* Drop zone */}
      <Paper
        variant="outlined"
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        sx={{
          p: 5,
          textAlign: 'center',
          cursor: 'pointer',
          borderStyle: 'dashed',
          borderWidth: 2,
          borderColor: dragActive ? 'primary.main' : 'divider',
          backgroundColor: dragActive ? 'action.hover' : 'background.paper',
          transition: 'all 0.2s ease',
          '&:hover': { borderColor: 'primary.light', backgroundColor: 'action.hover' },
        }}
      >
        <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
        <Typography variant="h6" color="text.secondary">
          Drag CSV files here
        </Typography>
        <Typography variant="body2" color="text.secondary">
          or click to browse — supports multiple files
        </Typography>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          multiple
          hidden
          onChange={(e) => {
            if (e.target.files) addFiles(e.target.files);
            e.target.value = '';
          }}
        />
      </Paper>

      {/* Pending files */}
      {pendingFiles.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Ready to upload ({pendingFiles.length} file{pendingFiles.length > 1 ? 's' : ''})
          </Typography>
          <Stack spacing={1}>
            {pendingFiles.map((f) => (
              <Paper
                key={f.name}
                variant="outlined"
                sx={{ px: 2, py: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <InsertDriveFileIcon fontSize="small" color="action" />
                  <Typography variant="body2">{f.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    ({formatFileSize(f.size)})
                  </Typography>
                </Box>
                <IconButton size="small" onClick={() => removePendingFile(f.name)}>
                  <DeleteOutlinedIcon fontSize="small" />
                </IconButton>
              </Paper>
            ))}
          </Stack>
          <Box sx={{ mt: 2, display: "flex", gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<CloudUploadIcon />}
              onClick={handleUpload}
              disabled={uploading}
            >
              Upload {pendingFiles.length} File{pendingFiles.length > 1 ? 's' : ''}
            </Button>
            <Button variant="outlined" color="inherit" onClick={() => setPendingFiles([])}>
              Clear All
            </Button>
          </Box>
        </Box>
      )}

      {/* Upload progress */}
      {uploading && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress variant="determinate" value={uploadProgress} sx={{ height: 8, borderRadius: 4 }} />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>
            Uploading... {uploadProgress}%
          </Typography>
        </Box>
      )}

      {uploadError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {uploadError}
        </Alert>
      )}

      {/* Uploaded files table */}
      {uploadedFiles.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Uploaded Files ({uploadedFiles.length})
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Filename</TableCell>
                  <TableCell align="right">Size</TableCell>
                  <TableCell align="right">Rows</TableCell>
                  <TableCell align="right">Columns</TableCell>
                  <TableCell>Uploaded</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {uploadedFiles.map((f) => (
                  <TableRow key={f.id}>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <InsertDriveFileIcon fontSize="small" color="success" />
                        {f.original_filename}
                      </Box>
                    </TableCell>
                    <TableCell align="right">{formatFileSize(f.file_size)}</TableCell>
                    <TableCell align="right">{f.row_count?.toLocaleString() ?? '—'}</TableCell>
                    <TableCell align="right">{f.column_count ?? '—'}</TableCell>
                    <TableCell>{formatDate(f.uploaded_at)}</TableCell>
                    <TableCell align="center">
                      <Tooltip title="Delete file">
                        <IconButton size="small" color="error" onClick={() => handleDeleteFile(f.id)}>
                          <DeleteOutlinedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Navigation */}
      <Box sx={{ mt: 3, display: "flex", justifyContent: "space-between" }}>
        <Button variant="outlined" onClick={() => setActiveStep(0)}>
          Back
        </Button>
        <Button
          variant="contained"
          disabled={uploadedFiles.length === 0}
          onClick={() => setActiveStep(2)}
        >
          Continue to Summary
        </Button>
      </Box>
    </Box>
  );

  const renderSummaryStep = () => {
    const totalSize = uploadedFiles.reduce((sum, f) => sum + f.file_size, 0);
    const totalRows = uploadedFiles.reduce((sum, f) => sum + (f.row_count ?? 0), 0);

    return (
      <Card sx={{ maxWidth: 700, mx: 'auto', mt: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <CheckCircleOutlinedIcon color="success" sx={{ fontSize: 32 }} />
            <Typography variant="h6">Migration Ready</Typography>
          </Box>
          <Stack spacing={2}>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Migration Name
              </Typography>
              <Typography>{run?.name}</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Environment
              </Typography>
              <Chip label={run?.environment} size="small" color="primary" variant="outlined" />
            </Box>
            {run?.description && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Description
                </Typography>
                <Typography variant="body2">{run.description}</Typography>
              </Box>
            )}
            <Box sx={{ display: "flex", gap: 4 }}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Files
                </Typography>
                <Typography variant="h5">{uploadedFiles.length}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Total Size
                </Typography>
                <Typography variant="h5">{formatFileSize(totalSize)}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Total Rows
                </Typography>
                <Typography variant="h5">{totalRows.toLocaleString()}</Typography>
              </Box>
            </Box>
            <Alert severity="success">
              Upload complete! Next: go to <strong>Validation</strong> to discover schemas and run data-quality checks, then proceed to migration.
            </Alert>
            <Button
              variant="outlined"
              startIcon={<AddCircleOutlinedIcon />}
              onClick={() => {
                // Reset for a new migration
                setActiveStep(0);
                setName('');
                setEnvironment('development');
                setDescription('');
                setRun(null);
                setPendingFiles([]);
                setUploadedFiles([]);
              }}
            >
              Start New Migration
            </Button>
          </Stack>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600 }} gutterBottom>
        New Migration
      </Typography>
      <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
        {STEPS.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {activeStep === 0 && renderConfigureStep()}
      {activeStep === 1 && renderUploadStep()}
      {activeStep === 2 && renderSummaryStep()}
    </Box>
  );
}
