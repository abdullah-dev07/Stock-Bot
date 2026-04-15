

import React from 'react';
import '../../styles/SidePanel.css';

function SidePanel({ children }) {
  return (
    <div className="side-panel">
      {children}
    </div>
  );
}

export default SidePanel;
