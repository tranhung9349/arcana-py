import config from '/Users/tranduyhung/.understand-anything/repo/understand-anything-plugin/packages/dashboard/vite.config.ts';
export default {
  ...config,
  root: '/Users/tranduyhung/.understand-anything/repo/understand-anything-plugin/packages/dashboard',
  cacheDir: '/Users/tranduyhung/Work/randomyst_numbers/.ua/dashboard-cache',
  server: { ...config.server, host: '127.0.0.1', open: false },
};
