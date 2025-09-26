import { createBrowserRouter, Navigate } from 'react-router-dom';
import App from './App';
import Login from './pages/Login';
import AuthCallback from './pages/AuthCallback';
import HomeWeekly from './pages/HomeWeekly';
import HomeMonthly from './pages/HomeMonthly';
import ProtectedRoute from './routes/ProtectedRoute';
import RootRedirect from './routes/RootRedirect';

const router = createBrowserRouter([
  {
    path: '/',
    element: <RootRedirect />,
  },
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/auth/callback',
    element: <AuthCallback />,
  },
  {
    path: '/home',
    element: (
      <ProtectedRoute>
        <App />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/home/weekly" replace />,
      },
      {
        path: 'weekly',
        element: <HomeWeekly />,
      },
      {
        path: 'monthly',
        element: <HomeMonthly />,
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);

export default router;
