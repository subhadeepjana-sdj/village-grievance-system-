import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UserPlus, AlertCircle, CheckCircle2, Building2, Lock, Mail, User, Phone, ShieldCheck } from 'lucide-react';

const RegisterPage = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('CITIZEN');
  const [village, setVillage] = useState('Gram Panchayat Chandanpur');
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!consent) {
      setError('Please agree to the privacy and public records notice to continue.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await register({ name, email, phone, password, role });
      setSuccess(true);
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-12 px-4 sm:px-6 lg:px-8 max-w-lg mx-auto space-y-6">
      
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-xl bg-[#153D32] text-[#D7F36A] flex items-center justify-center font-bold mx-auto shadow-sm">
          <Building2 className="w-6 h-6 text-[#D7F36A]" />
        </div>
        <h2 className="text-2xl font-heading font-extrabold text-[#17221F]">
          Create a Citizen Account
        </h2>
        <p className="text-xs text-[#69736D]">
          Register to submit grievances, receive SMS/email updates, and query village bylaws
        </p>
      </div>

      <div className="civic-card p-6 sm:p-8 bg-[#FFFFFF] space-y-6">
        
        {error && (
          <div className="p-3.5 rounded-xl bg-[#FEF2F2] border border-[#FECACA] text-[#991B1B] text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-3.5 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] text-[#065F46] text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>Account created successfully! Redirecting to login...</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-bold text-[#17221F] block">
              Full Legal Name
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-[#69736D] absolute left-3 top-3" />
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Rajesh Kumar"
                className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-[#E5E7DF] text-xs bg-[#FFFFFF] text-[#17221F] focus:outline-none focus:ring-2 focus:ring-[#153D32]"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-[#17221F] block">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#69736D] absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="rajesh@email.com"
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-[#E5E7DF] text-xs bg-[#FFFFFF] text-[#17221F] focus:outline-none focus:ring-2 focus:ring-[#153D32]"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-[#17221F] block">
                Mobile Number
              </label>
              <div className="relative">
                <Phone className="w-4 h-4 text-[#69736D] absolute left-3 top-3" />
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 98000 00000"
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-[#E5E7DF] text-xs bg-[#FFFFFF] text-[#17221F] focus:outline-none focus:ring-2 focus:ring-[#153D32]"
                />
              </div>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-bold text-[#17221F] block">
              Gram Panchayat / Village
            </label>
            <select
              value={village}
              onChange={(e) => setVillage(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border border-[#E5E7DF] text-xs bg-[#FFFFFF] text-[#17221F] focus:outline-none focus:ring-2 focus:ring-[#153D32]"
            >
              <option value="Gram Panchayat Chandanpur">Gram Panchayat Chandanpur (South 24 Parganas)</option>
              <option value="Gram Panchayat Diamond Harbour">Gram Panchayat Diamond Harbour</option>
              <option value="Gram Panchayat Kakdwip">Gram Panchayat Kakdwip</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-bold text-[#17221F] block">
              Password (min 8 characters)
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-[#69736D] absolute left-3 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2.5 rounded-lg border border-[#E5E7DF] text-xs bg-[#FFFFFF] text-[#17221F] focus:outline-none focus:ring-2 focus:ring-[#153D32]"
              />
            </div>
          </div>

          <div className="flex items-start gap-2.5 pt-2">
            <input
              type="checkbox"
              id="consent"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              className="mt-1 rounded text-[#153D32] focus:ring-[#153D32] border-[#E5E7DF]"
            />
            <label htmlFor="consent" className="text-xs text-[#69736D] leading-relaxed cursor-pointer">
              I agree to the <span className="text-[#153D32] underline font-medium">Privacy Notice</span> and acknowledge that civic grievance records are processed for public service delivery under Gram Panchayat governance.
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-civic-primary text-xs !py-3 font-bold mt-2 shadow-sm"
          >
            {loading ? 'Creating Account...' : 'Complete Citizen Registration'}
          </button>
        </form>

        <div className="border-t border-[#E5E7DF] pt-4 text-center text-xs text-[#69736D]">
          Already have an account?{' '}
          <Link to="/login" className="font-bold text-[#153D32] hover:underline">
            Sign In here
          </Link>
        </div>

      </div>

    </div>
  );
};

export default RegisterPage;
