import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import App from './App';
import HomePage from './pages/HomePage';
import StatusPage from './pages/StatusPage';
import ServicesPage from './pages/ServicesPage';
import ContactsPage from './pages/ContactsPage';
import './index.css';

const router = createBrowserRouter([
  {
    element: <App />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'status', element: <StatusPage /> },
      { path: 'services', element: <ServicesPage /> },
      { path: 'contacts', element: <ContactsPage /> },
    ],
  },
]);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
