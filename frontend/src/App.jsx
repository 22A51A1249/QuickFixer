import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';

import { Login } from './pages/Login';
import { EmployeeDashboard } from './pages/EmployeeDashboard';
import { TechnicianDashboard } from './pages/TechnicianDashboard';
import { AdminDashboard } from './pages/AdminDashboard';
import { Chat } from './pages/Chat';
import { SubmitTicket } from './pages/SubmitTicket';
import { MyTickets } from './pages/MyTickets';
import { TicketDetails } from './pages/TicketDetails';
import { KnowledgeBase } from './pages/KnowledgeBase';
import { AdminSettings } from './pages/AdminSettings';
import { Profile } from './pages/Profile';

// App Layout with Sidebar and Header
const AppLayout = () => {
  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content">
        <Header />
        <Outlet />
      </div>
    </div>
  );
};

// Root index redirect based on user role
const RootRedirect = () => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: 'var(--bg-primary)',
        color: 'var(--text-secondary)',
      }}>
        Loading QuickFixer workspace...
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role === 'admin') {
    return <Navigate to="/admin" replace />;
  }
  if (user.role === 'technician') {
    return <Navigate to="/technician" replace />;
  }
  return <Navigate to="/dashboard" replace />;
};

export const App = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Login Route */}
          <Route path="/login" element={<Login />} />

          {/* Protected Routes inside AppLayout */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            {/* Root Dispatcher */}
            <Route path="/" element={<RootRedirect />} />

            {/* Employee Accessible Routes */}
            <Route path="/dashboard" element={<EmployeeDashboard />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/tickets/new" element={<SubmitTicket />} />
            <Route path="/tickets" element={<MyTickets />} />
            <Route path="/tickets/history" element={<MyTickets showHistoryOnly={true} />} />
            <Route path="/tickets/:id" element={<TicketDetails />} />
            <Route path="/knowledge" element={<KnowledgeBase />} />
            <Route path="/profile" element={<Profile />} />

            {/* Technician Workspace Routes */}
            <Route
              path="/technician"
              element={
                <ProtectedRoute allowedRoles={['technician', 'admin']}>
                  <TechnicianDashboard defaultFilter="All Tickets" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/technician/tickets"
              element={
                <ProtectedRoute allowedRoles={['technician', 'admin']}>
                  <TechnicianDashboard defaultFilter="Assigned to Me" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/technician/team"
              element={
                <ProtectedRoute allowedRoles={['technician', 'admin']}>
                  <TechnicianDashboard defaultFilter="Team Tickets" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/technician/in-progress"
              element={
                <ProtectedRoute allowedRoles={['technician', 'admin']}>
                  <TechnicianDashboard defaultFilter="In Progress" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/technician/resolved"
              element={
                <ProtectedRoute allowedRoles={['technician', 'admin']}>
                  <TechnicianDashboard defaultFilter="Resolved" />
                </ProtectedRoute>
              }
            />

            {/* Administrator Console Routes */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminDashboard initialTab="overview" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/tickets"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminDashboard initialTab="tickets" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminDashboard initialTab="users" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/technicians"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminDashboard initialTab="technicians" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/teams"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminDashboard initialTab="teams" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/knowledge"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <KnowledgeBase />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/analytics"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminDashboard initialTab="overview" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/audit-logs"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminDashboard initialTab="audit" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/settings"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminSettings />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;

