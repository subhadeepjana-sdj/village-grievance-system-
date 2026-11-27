import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import CitizenDashboard from './pages/CitizenDashboard';
import SubmitComplaintPage from './pages/SubmitComplaintPage';
import TrackComplaintPage from './pages/TrackComplaintPage';
import AiAssistantPage from './pages/AiAssistantPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import PanchayatDashboard from './pages/PanchayatDashboard';
import DepartmentDashboard from './pages/DepartmentDashboard';
import AdminDashboard from './pages/AdminDashboard';
import ResearchDashboard from './pages/ResearchDashboard';
import CitizenServicesPage from './pages/citizen/CitizenServicesPage';
import AIMonitoringPage from './pages/admin/AIMonitoringPage';
import NotificationsPage from './pages/admin/NotificationsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppRoutes() {
  return (
    <Routes>
      {/* Primary Dashboard Route */}
      <Route path="/" element={<AdminDashboard />} />
      <Route path="/overview" element={<AdminDashboard />} />
      <Route path="/dashboard" element={<AdminDashboard />} />
      <Route path="/admin/dashboard" element={<AdminDashboard />} />
      <Route path="/admin-dashboard" element={<AdminDashboard />} />

      {/* Public / Landing & Auth */}
      <Route path="/landing" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      
      {/* Functional Redressal & Knowledge Pages */}
      <Route path="/knowledge-base" element={<KnowledgeBasePage />} />
      <Route path="/track" element={<TrackComplaintPage />} />
      <Route path="/submit" element={<SubmitComplaintPage />} />
      <Route path="/ai-assistant" element={<AiAssistantPage />} />
      <Route path="/research" element={<ResearchDashboard />} />
      <Route path="/admin/ai-monitoring" element={<AIMonitoringPage />} />
      <Route path="/admin/notifications" element={<NotificationsPage />} />
      <Route path="/notifications" element={<NotificationsPage />} />

      {/* Specialized Dashboards */}
      <Route path="/citizen/dashboard" element={<CitizenDashboard />} />
      <Route path="/citizen/complaints/new" element={<SubmitComplaintPage />} />
      <Route path="/citizen/complaints/:id" element={<TrackComplaintPage />} />
      <Route path="/citizen/ai-assistant" element={<AiAssistantPage />} />
      <Route path="/citizen/services" element={<CitizenServicesPage />} />
      <Route path="/panchayat/dashboard" element={<PanchayatDashboard />} />
      <Route path="/department/dashboard" element={<DepartmentDashboard />} />
      <Route path="/research/dashboard" element={<ResearchDashboard />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function AppContent() {
  const { user } = useAuth();

  // If user is authenticated, render with full-height left sidebar matching reference UI
  if (user) {
    return (
      <div className="min-h-screen flex bg-[#F0F4F9] text-[#1A202C]">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <Navbar />
          <main className="flex-1 overflow-x-hidden px-6 lg:px-8 pb-10">
            <AppRoutes />
          </main>
        </div>
      </div>
    );
  }

  // Public visitor layout: full-width top navbar and centered container main
  return (
    <div className="min-h-screen flex flex-col bg-[#F8FAFC] text-[#1A202C]">
      <Navbar />
      <main className="flex-1 px-4 sm:px-6 lg:px-8 py-8">
        <AppRoutes />
      </main>
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <AppContent />
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}
