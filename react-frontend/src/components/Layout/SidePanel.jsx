

import React from 'react';
import './SidePanel.css';

function SidePanel({ children }) {
  return (
    <div className="side-panel">
      {children}
    </div>
  );
}

export default SidePanel;
