import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  User, 
  Lock, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  Moon, 
  Sun, 
  Check, 
  AlertCircle,
  Sparkles,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import NeumorphicWaveLogo from '../components/NeumorphicWaveLogo';
import './LoginPage.css';

const DEMO_ACCOUNTS = [
  { role: 'CITIZEN', email: 'citizen@village.gov.in', label: 'Citizen', name: 'Rajesh Kumar', badge: 'Public' },
  { role: 'PANCHAYAT_STAFF', email: 'staff@village.gov.in', label: 'Panchayat Staff', name: 'Staff Anjali', badge: 'Triage' },
  { role: 'DEPARTMENT_OFFICIAL', email: 'official@water.gov.in', label: 'Water Officer', name: 'Officer Vikram', badge: 'Field' },
  { role: 'ADMIN', email: 'admin@village.gov.in', label: 'Admin', name: 'Divya Prasad', badge: 'Super' },
  { role: 'RESEARCHER', email: 'researcher@village.gov.in', label: 'Researcher', name: 'Dr. Sunita Sharma', badge: 'Research' }
];

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showDemoRoles, setShowDemoRoles] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [infoMessage, setInfoMessage] = useState('');

  const { login } = useAuth();
  const navigate = useNavigate();

  const redirectByRole = (role) => {
    switch (role) {
      case 'PANCHAYAT_STAFF':
        navigate('/panchayat/dashboard');
        break;
      case 'DEPARTMENT_OFFICIAL':
        navigate('/department/dashboard');
        break;
      case 'ADMIN':
        navigate('/admin/dashboard');
        break;
      case 'RESEARCHER':
        navigate('/research');
        break;
      default:
        navigate('/dashboard');
        break;
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!email || !password) {
      setError('Please enter your username/email and password.');
      return;
    }
    setError('');
    setInfoMessage('');
    setLoading(true);
    try {
      const data = await login(email, password);
      redirectByRole(data.role);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (demoEmail) => {
    setEmail(demoEmail);
    setPassword('Password123!');
    setError('');
    setInfoMessage('');
    setLoading(true);
    try {
      const data = await login(demoEmail, 'Password123!');
      redirectByRole(data.role);
    } catch (err) {
      setError(err.response?.data?.detail || 'Demo login failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = (e) => {
    e.preventDefault();
    setInfoMessage('Password reset link sent to registered email. For demo, use: Password123!');
    setTimeout(() => setInfoMessage(''), 6000);
  };

  const handleSocialClick = (provider) => {
    // Quick convenience: map Google to Citizen, Discord to Panchayat, Facebook to Admin or show alert
    if (provider === 'Google') {
      handleQuickLogin('citizen@village.gov.in');
    } else if (provider === 'Discord') {
      handleQuickLogin('staff@village.gov.in');
    } else {
      handleQuickLogin('admin@village.gov.in');
    }
  };

  return (
    <div className={`neumorphic-login-root ${isDarkMode ? 'dark' : ''}`}>
      {/* ─── Ambient Decorative Neumorphic Shapes ─── */}
      <div className="neu-ambient-ring-tl" />
      <div className="neu-ambient-sphere-tr" />
      <div className="neu-ambient-ring-bl" />
      
      {/* Bottom-right curved "MORE THAN A GAME" corner matching reference */}
      <div className="neu-ambient-corner-br hidden sm:flex">
        <div className="text-right tracking-widest text-[9px] font-bold leading-tight" style={{ color: 'var(--neu-text-muted)' }}>
          <div>MORE</div>
          <div>THAN</div>
          <div>A GAME</div>
          <div className="w-4 h-[2px] bg-slate-400 dark:bg-slate-600 ml-auto mt-1" />
        </div>
      </div>

      {/* ─── Top Right Moon / Sun Toggle ─── */}
      <button
        type="button"
        onClick={() => setIsDarkMode(!isDarkMode)}
        className="neu-theme-toggle"
        title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        aria-label="Toggle Theme"
      >
        {isDarkMode ? (
          <Sun className="w-5 h-5 text-amber-400 transition-transform duration-300 rotate-0 hover:rotate-90" />
        ) : (
          <Moon className="w-5 h-5 text-slate-800 transition-transform duration-300 -rotate-12 hover:rotate-0" />
        )}
      </button>

      {/* ─── Main Login Container ─── */}
      <div className="w-full max-w-[380px] sm:max-w-[400px] flex flex-col items-center z-10 px-2 space-y-6">
        
        {/* ─── 3D Wave Squircle Emblem ─── */}
        <div className="neu-brand-squircle mb-1">
          <NeumorphicWaveLogo size={70} className="w-[70px] h-[70px]" />
        </div>

        {/* ─── Title & Subtitle ─── */}
        <div className="text-center space-y-1.5">
          <h1 
            className="text-3xl sm:text-[34px] font-black tracking-tight"
            style={{ color: 'var(--neu-text-primary)' }}
          >
            Welcome Back
          </h1>
          <p 
            className="text-[13px] font-medium tracking-[0.18em]"
            style={{ color: 'var(--neu-text-secondary)' }}
          >
            Sign in to continue
          </p>
        </div>

        {/* ─── Notifications / Error Banner ─── */}
        {error && (
          <div className="w-full p-3 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-xs flex items-center gap-2.5 animate-fadeIn">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {infoMessage && (
          <div className="w-full p-3 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400 text-xs flex items-center gap-2.5 animate-fadeIn">
            <Sparkles className="w-4 h-4 shrink-0" />
            <span>{infoMessage}</span>
          </div>
        )}

        {/* ─── Credential Form ─── */}
        <form onSubmit={handleSubmit} className="w-full space-y-4">
          
          {/* Username / Email Input */}
          <div className="neu-input-wrapper">
            <User 
              className="w-5 h-5 shrink-0 transition-colors" 
              style={{ color: 'var(--neu-text-secondary)' }} 
            />
            <input
              type="text"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Username or Email"
              className="neu-input-field"
              autoComplete="username"
            />
          </div>

          {/* Password Input */}
          <div className="neu-input-wrapper">
            <Lock 
              className="w-5 h-5 shrink-0 transition-colors" 
              style={{ color: 'var(--neu-text-secondary)' }} 
            />
            <input
              type={showPassword ? 'text' : 'password'}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="neu-input-field"
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="p-1 focus:outline-none transition-colors"
              style={{ color: 'var(--neu-text-secondary)' }}
              title={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? (
                <EyeOff className="w-4 h-4 hover:opacity-80" />
              ) : (
                <Eye className="w-4 h-4 hover:opacity-80" />
              )}
            </button>
          </div>

          {/* Remember Me & Forgot Password Row */}
          <div className="flex items-center justify-between px-2 pt-0.5 text-xs font-semibold select-none">
            <label className="flex items-center gap-2.5 cursor-pointer">
              <div 
                className={`neu-checkbox ${rememberMe ? 'checked' : ''}`}
                onClick={() => setRememberMe(!rememberMe)}
              >
                {rememberMe && <Check className="w-3.5 h-3.5 text-white stroke-[3]" />}
              </div>
              <span style={{ color: 'var(--neu-text-secondary)' }}>
                Remember Me
              </span>
            </label>

            <button
              type="button"
              onClick={handleForgotPassword}
              className="font-bold transition-opacity hover:opacity-80"
              style={{ color: 'var(--neu-accent)' }}
            >
              Forgot Password?
            </button>
          </div>

          {/* Login Button with Arrow Badge */}
          <button
            type="submit"
            disabled={loading}
            className="neu-btn-login mt-2"
          >
            <span className="mx-auto text-[17px]">
              {loading ? 'Signing in...' : 'Login'}
            </span>
            <div className="neu-login-arrow-circle">
              <ArrowRight className="w-5 h-5 text-white stroke-[2.5]" />
            </div>
          </button>
        </form>

        {/* ─── "OR CONTINUE WITH" Divider ─── */}
        <div className="w-full flex items-center gap-3 pt-2">
          <div className="flex-1 h-[1.5px] bg-gradient-to-r from-transparent to-slate-300 dark:to-slate-700" />
          <span 
            className="text-[11px] font-bold tracking-[0.2em] whitespace-nowrap uppercase"
            style={{ color: 'var(--neu-text-secondary)' }}
          >
            Or Continue With
          </span>
          <div className="flex-1 h-[1.5px] bg-gradient-to-l from-transparent to-slate-300 dark:to-slate-700" />
        </div>

        {/* ─── Social Providers (Google, Discord, Facebook) ─── */}
        <div className="flex items-center justify-center gap-5 pt-1">
          {/* Google Button */}
          <button
            type="button"
            onClick={() => handleSocialClick('Google')}
            className="neu-social-btn"
            title="Sign in with Google (Demo: Citizen)"
          >
            <svg viewBox="0 0 24 24" className="w-6 h-6">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
            </svg>
          </button>

          {/* Discord Button */}
          <button
            type="button"
            onClick={() => handleSocialClick('Discord')}
            className="neu-social-btn"
            title="Sign in with Discord (Demo: Staff)"
          >
            <svg viewBox="0 0 24 24" className="w-6 h-6" fill="#5865F2">
              <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.929 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.894.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
            </svg>
          </button>

          {/* Facebook Button */}
          <button
            type="button"
            onClick={() => handleSocialClick('Facebook')}
            className="neu-social-btn"
            title="Sign in with Facebook (Demo: Admin)"
          >
            <svg viewBox="0 0 24 24" className="w-6 h-6" fill="#1877F2">
              <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
            </svg>
          </button>
        </div>

        {/* ─── Collapsible 1-Click Demo Accounts Switcher ─── */}
        <div className="w-full pt-1">
          <button
            type="button"
            onClick={() => setShowDemoRoles(!showDemoRoles)}
            className="w-full flex items-center justify-center gap-1.5 py-1.5 text-[11px] font-bold tracking-wider uppercase transition-colors hover:opacity-90"
            style={{ color: 'var(--neu-accent)' }}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>1-Click Demo Accounts</span>
            {showDemoRoles ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showDemoRoles && (
            <div className="mt-2.5 p-3 rounded-2xl space-y-2 neu-demo-accordion animate-fadeIn">
              <div className="text-[10px] font-semibold text-center pb-1" style={{ color: 'var(--neu-text-secondary)' }}>
                Select any verified village portal role to instant-login:
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {DEMO_ACCOUNTS.map((acc) => (
                  <button
                    key={acc.email}
                    type="button"
                    onClick={() => handleQuickLogin(acc.email)}
                    disabled={loading}
                    className="neu-demo-chip"
                  >
                    <div>
                      <div className="text-[11px] font-bold">{acc.label}</div>
                      <div className="text-[9px] font-normal" style={{ color: 'var(--neu-text-muted)' }}>{acc.name}</div>
                    </div>
                    <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 font-bold">
                      {acc.badge}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ─── Bottom Footer Tagline ─── */}
        <div className="pt-4 text-center">
          <p 
            className="text-[10px] sm:text-[11px] font-bold tracking-[0.28em] uppercase select-none"
            style={{ color: 'var(--neu-text-secondary)' }}
          >
            PLAY &bull; COMPETE &bull; GROW TOGETHER
          </p>
          <div className="mt-2 text-[11px]" style={{ color: 'var(--neu-text-muted)' }}>
            New user?{' '}
            <Link 
              to="/register" 
              className="font-bold underline hover:opacity-80"
              style={{ color: 'var(--neu-accent)' }}
            >
              Register here
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
};

export default LoginPage;
