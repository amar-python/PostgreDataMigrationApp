import HistoryIcon from '@mui/icons-material/History';
import PagePlaceholder from './PagePlaceholder';

export default function History() {
  return (
    <PagePlaceholder
      title="History"
      icon={<HistoryIcon />}
      description="Audit the full history of migration and validation activity over time."
    />
  );
}
