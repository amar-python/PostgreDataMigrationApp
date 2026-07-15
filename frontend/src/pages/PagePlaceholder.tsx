import type { ReactNode } from 'react';
import { Box, Card, CardContent, Chip, Typography } from '@mui/material';

interface PagePlaceholderProps {
  title: string;
  icon: ReactNode;
  description?: string;
}

/**
 * Empty-state card used by every route until real functionality lands.
 * Keeps the shell looking finished while signalling work-in-progress.
 */
export default function PagePlaceholder({
  title,
  icon,
  description,
}: PagePlaceholderProps) {
  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
        <Box sx={{ color: 'primary.main', display: 'flex' }}>{icon}</Box>
        <Typography variant="h4">{title}</Typography>
      </Box>

      <Card
        variant="outlined"
        sx={{
          borderColor: 'divider',
          maxWidth: 720,
        }}
      >
        <CardContent sx={{ py: 6, textAlign: 'center' }}>
          <Box sx={{ color: 'text.secondary', mb: 2, '& svg': { fontSize: 48 } }}>
            {icon}
          </Box>
          <Chip label="Coming Soon" color="primary" variant="outlined" sx={{ mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {title} — Coming Soon
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {description ??
              'This section is part of the Migration Evaluation Platform and will be available in an upcoming release.'}
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
