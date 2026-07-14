import StorageIcon from '@mui/icons-material/Storage';
import PagePlaceholder from './PagePlaceholder';

export default function MigrationRuns() {
  return (
    <PagePlaceholder
      title="Migration Runs"
      icon={<StorageIcon />}
      description="Browse and monitor active and completed CSV → PostgreSQL migration runs."
    />
  );
}
