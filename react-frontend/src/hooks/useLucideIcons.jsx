
import { useEffect } from 'react';
import lucide from 'lucide-react'; 

const useLucideIcons = () => {
  useEffect(() => {
    
    
    if (window.lucide) {
      window.lucide.createIcons();
    }
  }, []);
};

export default useLucideIcons;
