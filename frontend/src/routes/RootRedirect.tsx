import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getStoredToken } from '../utils/storage';

const RootRedirect = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const token = getStoredToken();
    if (token) {
      navigate('/home/weekly', { replace: true });
    } else {
      navigate('/login', { replace: true });
    }
  }, [navigate]);

  return null;
};

export default RootRedirect;
