
import { useEffect } from 'react';
import lucide from 'lucide-react'; // You may need to install this: npm install lucide-react

const useLucideIcons = () => {
  useEffect(() => {
    // This is a workaround for the vanilla JS version of lucide
    // In a pure React app, you'd import icons as components.
    if (window.lucide) {
      window.lucide.createIcons();
    }
  }, []);
};

export default useLucideIcons;
