import DashboardIcon from '@mui/icons-material/Dashboard';
import PagePlaceholder from './PagePlaceholder';

export default function Dashboard() {
  return (
    <PagePlaceholder
      title="Dashboard"
      icon={<DashboardIcon />}
      description="An at-a-glance overview of migration activity, health, and key metrics will appear here."
    />
  );
}
