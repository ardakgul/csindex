import React from 'react';
import { createRoot } from 'react-dom/client';
import Dashboard from './pages/Dashboard.jsx';
import CloudyShinyPalantirDashboard from './CloudyShinyPalantirDashboard.jsx';
import './styles.css';

const params = new URLSearchParams(window.location.search);
const usePalantir = params.get('palantir') === '1';

createRoot(document.getElementById('root')).render(usePalantir ? <CloudyShinyPalantirDashboard /> : <Dashboard />);