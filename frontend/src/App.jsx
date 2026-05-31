import { Outlet } from 'react-router-dom';
import BottomNav from './components/BottomNav';
import { ToastProvider } from './components/Toast';

export default function App() {
  return (
    <ToastProvider>
      <Outlet />
      <BottomNav />
    </ToastProvider>
  );
}
