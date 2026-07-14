import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutlineOutlined';
import PagePlaceholder from './PagePlaceholder';

export default function NewMigration() {
  return (
    <PagePlaceholder
      title="New Migration"
      icon={<AddCircleOutlineIcon />}
      description="Configure and launch a new migration by uploading source data and selecting a target."
    />
  );
}
