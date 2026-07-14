import FactCheckIcon from '@mui/icons-material/FactCheck';
import PagePlaceholder from './PagePlaceholder';

export default function Validation() {
  return (
    <PagePlaceholder
      title="Validation"
      icon={<FactCheckIcon />}
      description="Review data-quality checks and validation assertions against migrated datasets."
    />
  );
}
