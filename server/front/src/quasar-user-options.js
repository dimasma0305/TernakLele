import "./styles/quasar.scss";
import "@quasar/extras/material-icons/material-icons.css";
import "@quasar/extras/fontawesome-v5/fontawesome-v5.css";
import "@quasar/extras/material-icons-outlined/material-icons-outlined.css";

// To be used on app.use(Quasar, { ... })
export default {
  config: {
    dark: 'auto',
    brand: {
      primary: '#4f46e5',
      secondary: '#10b981',
      accent: '#8b5cf6',
      dark: '#121212',
      positive: '#22c55e',
      negative: '#ef4444',
      info: '#3b82f6',
      warning: '#f59e0b'
    }
  },
  plugins: {},
};
