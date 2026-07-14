import AssessmentIcon from '@mui/icons-material/Assessment';
import PagePlaceholder from './PagePlaceholder';

export default function Reports() {
  return (
    <PagePlaceholder
      title="Reports"
      icon={<AssessmentIcon />}
      description="Generate and export detailed evaluation reports for each migration run."
    />
  );
}
