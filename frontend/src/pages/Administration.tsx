import SettingsIcon from '@mui/icons-material/Settings';
import PagePlaceholder from './PagePlaceholder';

export default function Administration() {
  return (
    <PagePlaceholder
      title="Administration"
      icon={<SettingsIcon />}
      description="Manage connections, users, and platform configuration settings."
    />
  );
}
