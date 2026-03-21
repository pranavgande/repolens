import { createBrowserRouter } from 'react-router';
import { Landing } from './pages/Landing';
import { Processing } from './pages/Processing';
import { Results } from './pages/Results';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Landing />,
  },
  {
    path: '/processing',
    element: <Processing />,
  },
  {
    path: '/results',
    element: <Results />,
  },
]);
