import { createTheme } from '@mui/material/styles';

/**
 * MEP theme — light, clean, professional. Modeled on the Azure Portal:
 * Azure blue primary (#0078D4), neutral greys, subtle borders, and a
 * comfortable density for an enterprise SaaS product.
 */
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#0078D4', // Azure blue
      dark: '#005A9E',
      light: '#2B88D8',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#5C2D91',
    },
    success: {
      main: '#107C10',
    },
    error: {
      main: '#D13438',
    },
    background: {
      default: '#F3F2F1', // Azure Portal content grey
      paper: '#FFFFFF',
    },
    text: {
      primary: '#201F1E',
      secondary: '#605E5C',
    },
    divider: '#EDEBE9',
  },
  typography: {
    fontFamily:
      '"Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    subtitle1: { fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: {
    borderRadius: 4,
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#FFFFFF',
          color: '#201F1E',
          boxShadow: 'none',
          borderBottom: '1px solid #EDEBE9',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          '&.Mui-selected': {
            backgroundColor: 'rgba(255,255,255,0.12)',
          },
          '&.Mui-selected:hover': {
            backgroundColor: 'rgba(255,255,255,0.18)',
          },
        },
      },
    },
  },
});

export default theme;
