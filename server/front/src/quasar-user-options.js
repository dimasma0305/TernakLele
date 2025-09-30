import "./styles/quasar.scss";
import "@quasar/extras/material-icons/material-icons.css";
import "@quasar/extras/fontawesome-v5/fontawesome-v5.css";
import { Dark, Notify } from 'quasar';

// To be used on app.use(Quasar, { ... })
export default {
  config: {
    notify: {
      position: 'top-right',
      timeout: 3000,
      textColor: 'white',
      actions: [{ icon: 'close', color: 'white' }]
    }
  },
  plugins: {
    Dark,
    Notify
  },
};
