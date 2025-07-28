// FILE: react-frontend/src/components/Layout/SidePanel.js

import React from 'react';

// This is a simple "wrapper" component.
// The special 'children' prop will render any components nested inside <SidePanel> in App.js
function SidePanel({ children }) {
  return (
    <div className="side-panel">
      {children}
    </div>
  );
}

export default SidePanel;
