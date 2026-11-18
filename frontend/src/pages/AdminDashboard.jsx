import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { adminService } from '../services/adminService';
import { ticketService } from '../services/ticketService';
import { StatCard } from '../components/StatCard';
import { TicketTable } from '../components/TicketTable';
import {
  Users,
  Ticket,
  CheckCircle,
  AlertOctagon,
  UserCheck,
  TrendingUp,
  ShieldCheck,
  UserPlus,
  RefreshCw,
  Edit,
  Power,
  Search,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

const CHART_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4'];

export const AdminDashboard = ({ initialTab = 'overview' }) => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState(initialTab);
  const [stats, setStats] = useState(null);
  const [allTickets, setAllTickets] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  // User creation form modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newPassword, setNewPassword] = useState('Password123!');
  const [newRole, setNewRole] = useState('employee');
  const [newTeam, setNewTeam] = useState('General Service Desk');
  const [createError, setCreateError] = useState('');
  const [createSuccess, setCreateSuccess] = useState('');

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setIsLoading(true);
    try {
      const [statsData, ticketsData, usersData, logsData] = await Promise.all([
        adminService.getDashboardStats(),
        ticketService.listTickets(),
        adminService.listUsers(),
        adminService.listAuditLogs(100),
      ]);
      setStats(statsData);
      setAllTickets(ticketsData);
      setAllUsers(usersData);
      setAuditLogs(logsData);
    } catch (err) {
      console.error('Failed to load admin dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setCreateError('');
    setCreateSuccess('');
    try {
      await adminService.createUser({
        username: newUsername.trim(),
        email: newEmail.trim(),
        full_name: newFullName.trim(),
        password: newPassword,
        role: newRole,
        team: newRole === 'technician' ? newTeam : null,
      });
      setCreateSuccess(`User "${newUsername}" created successfully!`);
      setNewUsername('');
      setNewEmail('');
      setNewFullName('');
      setShowCreateModal(false);
      // Reload users
      const freshUsers = await adminService.listUsers();
      setAllUsers(freshUsers);
    } catch (err) {
      setCreateError(err.response?.data?.detail || 'Failed to create user account.');
    }
  };

  const handleToggleUserStatus = async (targetUser) => {
    try {
      await adminService.updateUserStatus(targetUser.id, !targetUser.is_active);
      const freshUsers = await adminService.listUsers();
      setAllUsers(freshUsers);
    } catch (err) {
      alert('Failed to toggle status: ' + (err.response?.data?.detail || err.message));
    }
  };

  // Prepare chart datasets
  const categoryChartData = stats?.category_distribution
    ? Object.entries(stats.category_distribution).map(([name, count]) => ({ name, count }))
    : [];

  const priorityChartData = stats?.priority_distribution
    ? Object.entries(stats.priority_distribution).map(([name, count]) => ({ name, value: count }))
    : [];

  const teamChartData = stats?.team_distribution
    ? Object.entries(stats.team_distribution).map(([name, count]) => ({ name, count }))
    : [];

  return (
    <div className="page-body">
      {/* Header Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.75rem',
      }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
            👑 Central Administrator Operations Console
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Enterprise oversight of service desk incidents, user lifecycles, and security audit logs.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.65rem' }}>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
            style={{ fontSize: '0.85rem' }}
          >
            <UserPlus size={15} />
            <span>Create User Account</span>
          </button>
          <button
            onClick={loadAllData}
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem' }}
            title="Refresh dashboard metrics"
          >
            <RefreshCw size={15} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* High-Level Metric KPIs */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '1rem',
        marginBottom: '1.75rem',
      }}>
        <StatCard
          title="Total Tickets"
          value={stats?.total_tickets || 0}
          icon={Ticket}
          color="var(--accent-primary)"
        />
        <StatCard
          title="Open Queue"
          value={stats?.open_tickets || 0}
          icon={AlertOctagon}
          color="var(--color-warning)"
          delta={`${stats?.open_tickets || 0} active`}
        />
        <StatCard
          title="Critical Tickets"
          value={stats?.critical_tickets || 0}
          icon={AlertOctagon}
          color="var(--color-danger)"
          delta="Urgent incident triage"
        />
        <StatCard
          title="Resolved"
          value={stats?.resolved_tickets || 0}
          icon={CheckCircle}
          color="var(--color-success)"
          subtext={`${stats?.resolution_rate || 0}% resolution rate`}
        />
        <StatCard
          title="Employees"
          value={stats?.total_employees || 0}
          icon={Users}
          color="#8B5CF6"
        />
        <StatCard
          title="Technicians"
          value={stats?.total_technicians || 0}
          icon={UserCheck}
          color="#06B6D4"
        />
      </div>

      {/* Tab Navigation */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        marginBottom: '1.5rem',
        borderBottom: '1px solid var(--border-subtle)',
        paddingBottom: '0.5rem',
      }}>
        {[
          { id: 'overview', label: '📊 Overview' },
          { id: 'tickets', label: '🎫 All Tickets' },
          { id: 'users', label: '👥 User Directory' },
          { id: 'technicians', label: '🛠️ Technicians' },
          { id: 'teams', label: '🗂️ Support Teams' },
          { id: 'audit', label: '📜 Security Audit Logs' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              background: 'transparent',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem',
              fontWeight: activeTab === tab.id ? 700 : 500,
              color: activeTab === tab.id ? 'var(--accent-primary)' : 'var(--text-secondary)',
              backgroundColor: activeTab === tab.id ? 'rgba(59, 130, 246, 0.12)' : 'transparent',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: OVERVIEW CHARTS */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem' }}>
          {/* Incidents by Category */}
          <div className="card">
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1.25rem' }}>
              Incidents by Problem Category
            </h3>
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryChartData}>
                  <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} interval={0} angle={-15} textAnchor="end" height={50} />
                  <YAxis stroke="var(--text-muted)" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-subtle)', color: '#FFF' }}
                  />
                  <Bar dataKey="count" fill="var(--accent-primary)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Incidents by Priority Distribution */}
          <div className="card">
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1.25rem' }}>
              Incident Priority Distribution
            </h3>
            <div style={{ width: '100%', height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={priorityChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {priorityChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-subtle)', color: '#FFF' }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Team Queue Workload */}
          <div className="card" style={{ gridColumn: '1 / -1' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1.25rem' }}>
              Team Queue Dispatch & Workload Distribution
            </h3>
            <div style={{ width: '100%', height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={teamChartData} layout="vertical">
                  <XAxis type="number" stroke="var(--text-muted)" fontSize={11} />
                  <YAxis dataKey="name" type="category" stroke="var(--text-muted)" fontSize={11} width={180} />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-subtle)', color: '#FFF' }}
                  />
                  <Bar dataKey="count" fill="#10B981" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ALL TICKETS WORKSPACE */}
      {activeTab === 'tickets' && (
        <TicketTable
          tickets={allTickets}
          isLoading={isLoading}
          showRequester={true}
          showAssignee={true}
          baseDetailPath="/tickets"
        />
      )}

      {/* TAB 3 & 4: USER & TECHNICIAN MANAGEMENT */}
      {(activeTab === 'users' || activeTab === 'technicians') && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>
              {activeTab === 'technicians'
                ? `Designated Technicians (${allUsers.filter(u => u.role === 'technician').length} accounts)`
                : `Enterprise User Directory (${allUsers.length} accounts)`}
            </h3>
            <button
              onClick={() => {
                if (activeTab === 'technicians') setNewRole('technician');
                setShowCreateModal(true);
              }}
              className="btn btn-primary"
              style={{ fontSize: '0.8rem' }}
            >
              <UserPlus size={14} />
              <span>{activeTab === 'technicians' ? 'Add Technician' : 'Add New User'}</span>
            </button>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>User ID</th>
                  <th>Full Name</th>
                  <th>Username</th>
                  <th>Corporate Email</th>
                  <th>Role</th>
                  <th>Queue / Team</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {allUsers
                  .filter(u => activeTab === 'technicians' ? u.role === 'technician' : true)
                  .map((u) => (
                  <tr key={u.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-primary)' }}>
                      {u.id}
                    </td>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {u.full_name}
                    </td>
                    <td>{u.username}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{u.email}</td>
                    <td>
                      <span style={{
                        padding: '0.15rem 0.5rem',
                        borderRadius: 'var(--radius-full)',
                        fontSize: '0.74rem',
                        fontWeight: 700,
                        backgroundColor: u.role === 'admin' ? 'rgba(245, 158, 11, 0.15)' : u.role === 'technician' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(22, 163, 74, 0.15)',
                        color: u.role === 'admin' ? '#FBBF24' : u.role === 'technician' ? '#60A5FA' : '#4ADE80',
                        textTransform: 'capitalize'
                      }}>
                        {u.role}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{u.team || '—'}</td>
                    <td>
                      <span style={{
                        fontSize: '0.74rem',
                        fontWeight: 600,
                        color: u.is_active ? 'var(--color-success)' : 'var(--color-danger)'
                      }}>
                        {u.is_active ? '🟢 Active' : '🔴 Deactivated'}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        onClick={() => handleToggleUserStatus(u)}
                        disabled={u.id === user.id}
                        className="btn btn-secondary"
                        style={{ padding: '0.25rem 0.6rem', fontSize: '0.72rem' }}
                        title={u.is_active ? 'Deactivate Account' : 'Activate Account'}
                      >
                        <Power size={12} color={u.is_active ? 'var(--color-danger)' : 'var(--color-success)'} />
                        <span>{u.is_active ? 'Deactivate' : 'Activate'}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: TEAM MANAGEMENT */}
      {activeTab === 'teams' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>
            🗂️ Support Team Queue Workload & Technician Allocation
          </h3>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Support Team / Queue</th>
                  <th>Assigned Technicians</th>
                  <th>Total Active Incidents</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {teamChartData.map((t, idx) => {
                  const techList = allUsers.filter(u => u.role === 'technician' && u.team && u.team.toLowerCase().includes(t.name.toLowerCase()));
                  return (
                    <tr key={idx}>
                      <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                        {t.name}
                      </td>
                      <td>
                        {techList.length > 0 ? (
                          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                            {techList.map(tech => (
                              <span key={tech.id} style={{
                                padding: '0.1rem 0.5rem',
                                borderRadius: 'var(--radius-full)',
                                backgroundColor: 'rgba(59, 130, 246, 0.15)',
                                color: '#60A5FA',
                                fontSize: '0.74rem'
                              }}>
                                🛠️ {tech.full_name}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>Tier 1 Pool</span>
                        )}
                      </td>
                      <td>
                        <span style={{
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 700,
                          color: t.count > 5 ? 'var(--color-warning)' : 'var(--accent-primary)',
                        }}>
                          {t.count} tickets
                        </span>
                      </td>
                      <td>
                        <span style={{
                          padding: '0.15rem 0.5rem',
                          borderRadius: 'var(--radius-full)',
                          fontSize: '0.74rem',
                          fontWeight: 700,
                          backgroundColor: 'var(--color-success-bg)',
                          color: '#4ADE80',
                        }}>
                          Operational
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 6: AUDIT LOGS */}
      {activeTab === 'audit' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>
            Security Audit Trail & Authentication Events
          </h3>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action</th>
                  <th>Actor / Username</th>
                  <th>Resource Type</th>
                  <th>Resource ID</th>
                  <th>IP Address</th>
                  <th>Event Details</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log, idx) => (
                  <tr key={idx}>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {log.timestamp?.substring(0, 19).replace('T', ' ')}
                    </td>
                    <td>
                      <span style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.74rem',
                        fontWeight: 700,
                        color: log.action.includes('SUCCESS') ? 'var(--color-success)' : log.action.includes('BLOCKED') || log.action.includes('FAIL') ? 'var(--color-danger)' : 'var(--accent-primary)',
                      }}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600 }}>{log.username || 'System'}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{log.resource_type || '—'}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{log.resource_id || '—'}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>{log.ip_address || '127.0.0.1'}</td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{log.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create User Account Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '1rem',
          zIndex: 1000,
        }}>
          <div className="card" style={{ maxWidth: '480px', width: '100%', padding: '2rem' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '0.35rem' }}>
              Create Enterprise Account
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
              Provision a new employee or technician identity in the QuickFixer user directory.
            </p>

            {createError && (
              <div style={{
                padding: '0.65rem',
                backgroundColor: 'var(--color-danger-bg)',
                border: '1px solid var(--color-danger-border)',
                borderRadius: 'var(--radius-md)',
                color: '#F87171',
                fontSize: '0.8rem',
                marginBottom: '1rem',
              }}>
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateUser}>
              <div className="form-group">
                <label className="form-label">Username *</label>
                <input
                  type="text"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  placeholder="e.g. jsmith"
                  className="input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Corporate Email *</label>
                <input
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="jsmith@company.com"
                  className="input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Full Name *</label>
                <input
                  type="text"
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  placeholder="John Smith"
                  className="input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Initial Password *</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Role Assignment *</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  className="select"
                >
                  <option value="employee">Employee</option>
                  <option value="technician">Technician</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>

              {newRole === 'technician' && (
                <div className="form-group">
                  <label className="form-label">Designated Support Queue</label>
                  <select
                    value={newTeam}
                    onChange={(e) => setNewTeam(e.target.value)}
                    className="select"
                  >
                    <option value="General Service Desk">General Service Desk</option>
                    <option value="NetOps & Network Infrastructure">NetOps & Network Infrastructure</option>
                    <option value="Deskside & Hardware Support">Deskside & Hardware Support</option>
                    <option value="Identity & Access Management (IAM)">Identity & Access Management (IAM)</option>
                    <option value="Security Operations Center (SOC)">Security Operations Center (SOC)</option>
                  </select>
                </div>
              )}

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn btn-ghost"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                >
                  Provision User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

