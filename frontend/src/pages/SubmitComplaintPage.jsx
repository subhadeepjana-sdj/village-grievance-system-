import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import { 
  PlusCircle, 
  CheckCircle2, 
  AlertCircle, 
  Upload, 
  MapPin, 
  FileText, 
  Layers, 
  ArrowRight, 
  ArrowLeft,
  Droplet,
  Construction,
  Trash2,
  Zap,
  Building,
  Award,
  HelpCircle,
  Camera,
  Check,
  Copy,
  Search,
  Bot
} from 'lucide-react';

const CATEGORIES = [
  { id: 'Water Supply', label: 'Water Supply', desc: 'Contaminated water, pipe leaks, tube wells, tanker requests', icon: Droplet },
  { id: 'Roads & Infrastructure', label: 'Roads & Bridges', desc: 'Potholes, broken roads, streetlights, drainage blockages', icon: Construction },
  { id: 'Sanitation', label: 'Sanitation & Hygiene', desc: 'Public toilets, open sewers, pesticide spraying', icon: Trash2 },
  { id: 'Electricity & Power', label: 'Electricity & Power', desc: 'Transformer failures, power outages, loose wires', icon: Zap },
  { id: 'Waste Management', label: 'Waste Management', desc: 'Overflowing bins, illegal dumping, garbage collection', icon: Trash2 },
  { id: 'Public Facilities', label: 'Public Facilities', desc: 'Primary schools, Anganwadi, health centers, community halls', icon: Building },
  { id: 'Government Schemes', label: 'Welfare Schemes', desc: 'PM-Kisan, PMAY housing, pensions, ration distribution', icon: Award },
  { id: 'Other', label: 'Other Inquiries', desc: 'General Gram Panchayat matters not covered above', icon: HelpCircle }
];

const SubmitComplaintPage = () => {
  const [step, setStep] = useState(1);
  const [category, setCategory] = useState('Water Supply');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('MEDIUM');
  const [location, setLocation] = useState('');
  const [ward, setWard] = useState('Ward 04');
  const [file, setFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [submittedComplaint, setSubmittedComplaint] = useState(null);
  const [copied, setCopied] = useState(false);

  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      if (selectedFile.type.startsWith('image/')) {
        setFilePreview(URL.createObjectURL(selectedFile));
      } else {
        setFilePreview(null);
      }
    }
  };

  const handleNext = (e) => {
    e.preventDefault();
    if (step === 2) {
      if (!title.trim() || !description.trim()) {
        setError('Please provide both a grievance summary title and detailed explanation.');
        return;
      }
      if (description.trim().length < 20) {
        setError('Please provide at least 20 characters describing the grievance.');
        return;
      }
    }
    if (step === 3 && !location.trim()) {
      setError('Please provide a specific street, landmark, or location.');
      return;
    }
    setError('');
    setStep(prev => prev + 1);
  };

  const handleBack = () => {
    setError('');
    setStep(prev => prev - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const fullLocation = `${ward}, ${location.trim()}`;
      const formData = new FormData();
      formData.append('category', category);
      formData.append('title', title.trim());
      formData.append('description', description.trim());
      formData.append('priority', priority);
      formData.append('location', fullLocation);
      if (file) {
        formData.append('file', file);
      }

      const res = await api.post('/complaints', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setSubmittedComplaint(res.data);
      setStep(6); // Step 6: Confirmation Screen
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit grievance. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="text-center space-y-1.5">
        <h1 className="text-2xl sm:text-3xl font-heading font-extrabold text-[#17221F]">
          Submit a Village Grievance
        </h1>
        <p className="text-xs text-[#69736D]">
          Your grievance is tracked publicly with SLA audit logs and verified through AI records.
        </p>
      </div>

      {/* 6-Step Visual Progress Indicator */}
      <div className="civic-card p-4 sm:p-5 bg-[#FFFFFF] space-y-2">
        <div className="flex items-center justify-between text-xs font-bold text-[#69736D] pb-1">
          <span>Step {step} of 6</span>
          <span className="text-[#153D32]">
            {step === 1 && '1. Choose Category'}
            {step === 2 && '2. Grievance Details'}
            {step === 3 && '3. Ward & Location'}
            {step === 4 && '4. Photo & Evidence'}
            {step === 5 && '5. Final Review'}
            {step === 6 && '6. Lodged Successfully'}
          </span>
        </div>

        {/* Segmented Progress Bar */}
        <div className="grid grid-cols-6 gap-1.5 h-2">
          {[1, 2, 3, 4, 5, 6].map((s) => (
            <div
              key={s}
              className={`rounded-full transition-all ${
                s <= step ? 'bg-[#153D32]' : 'bg-[#E5E7DF]'
              } ${s === step ? 'ring-2 ring-[#D7F36A]' : ''}`}
            />
          ))}
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-[#FEF2F2] border border-[#FECACA] text-[#991B1B] text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Step Wizard Card */}
      <div className="civic-card p-6 sm:p-8 bg-[#FFFFFF] space-y-6">
        
        {/* ================= STEP 1: CATEGORY SELECTION ================= */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="space-y-1">
              <h2 className="text-base font-heading font-bold text-[#17221F]">
                Select the Category of your Issue
              </h2>
              <p className="text-xs text-[#69736D]">
                Routing to the correct Panchayat department ensures faster assignment and strict SLA compliance.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              {CATEGORIES.map((cat) => {
                const Icon = cat.icon;
                const isSelected = category === cat.id;
                return (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => setCategory(cat.id)}
                    className={`p-3.5 rounded-xl border text-left transition cursor-pointer flex items-start gap-3 ${
                      isSelected
                        ? 'bg-[#EFF5EF] border-[#153D32] ring-1 ring-[#153D32]'
                        : 'bg-[#FFFFFF] border-[#E5E7DF] hover:border-[#69736D]'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                      isSelected ? 'bg-[#153D32] text-[#D7F36A]' : 'bg-[#F7F6F0] text-[#153D32]'
                    }`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="space-y-0.5">
                      <div className="text-xs font-bold text-[#17221F]">{cat.label}</div>
                      <div className="text-[11px] text-[#69736D] leading-tight line-clamp-2">{cat.desc}</div>
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="button"
                onClick={handleNext}
                className="btn-civic-primary text-xs !py-2.5 !px-5"
              >
                <span>Continue to Details</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 2: PROBLEM DETAILS ================= */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="space-y-1">
              <h2 className="text-base font-heading font-bold text-[#17221F]">
                Describe the Grievance
              </h2>
              <p className="text-xs text-[#69736D]">
                Be as clear as possible so municipal workers can inspect the issue without delay.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <div className="space-y-1">
                <label className="text-xs font-bold text-[#17221F] block">
                  Title / Issue Summary *
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Dirty Brown Tap Water from Main Overhead Pipe in Ward 4"
                  className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E7DF] text-xs bg-[#FFFFFF] text-[#17221F] focus:outline-none focus:ring-2 focus:ring-[#153D32]"
                />
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <label className="font-bold text-[#17221F]">
                    Detailed Explanation *
                  </label>
                  <span className="text-[#69736D] text-[11px]">
                    {description.length} characters (min 20)
                  </span>
                </div>
                <textarea
                  required
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Explain when the problem started, how many households are affected, and any previous attempts made..."
                  className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E7DF] text-xs bg-[#FFFFFF] text-[#17221F] focus:outline-none focus:ring-2 focus:ring-[#153D32] leading-relaxed"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-[#17221F] block">
                  Severity / Urgency Level
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {['LOW', 'MEDIUM', 'HIGH'].map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setPriority(p)}
                      className={`py-2 text-xs font-bold rounded-lg border transition cursor-pointer ${
                        priority === p
                          ? 'bg-[#153D32] text-[#FFFFFF] border-[#153D32]'
                          : 'bg-[#FFFFFF] text-[#69736D] border-[#E5E7DF] hover:bg-[#F7F6F0]'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-4 flex items-center justify-between">
              <button
                type="button"
                onClick={handleBack}
                className="btn-civic-secondary text-xs !py-2.5 !px-4"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button
                type="button"
                onClick={handleNext}
                className="btn-civic-primary text-xs !py-2.5 !px-5"
              >
                <span>Continue to Location</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 3: LOCATION & WARD ================= */}
        {step === 3 && (
          <div className="space-y-4">
            <div className="space-y-1">
              <h2 className="text-base font-heading font-bold text-[#17221F]">
                Where is the Issue Located?
              </h2>
              <p className="text-xs text-[#69736D]">
                Specify the exact Gram Panchayat Ward and prominent landmarks.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <div className="space-y-1">
                <label className="text-xs font-bold text-[#17221F] block">
                  Panchayat Ward
                </label>
                <select
                  value={ward}
                  onChange={(e) => setWard(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-[#E5E7DF] text-xs bg-[#FFFFFF] text-[#17221F] focus:outline-none focus:ring-2 focus:ring-[#153D32]"
                >
                  <option value="Ward 01">Ward 01 (North Para & Station Road)</option>
                  <option value="Ward 02">Ward 02 (Primary School & Hospital Lane)</option>
                  <option value="Ward 03">Ward 03 (South Bazar & Post Office)</option>
                  <option value="Ward 04">Ward 04 (Near Temple Lane & Tube Well 2)</option>
                  <option value="Ward 05">Ward 05 (East Canal Road)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-[#17221F] block">
                  Street, House Number, or Landmark *
                </label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-[#69736D] absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="e.g. Opposite Kali Mandir, near House 42 / Pole 18"
                    className="w-full pl-9 pr-3.5 py-2.5 rounded-lg border border-[#E5E7DF] text-xs bg-[#FFFFFF] text-[#17221F] focus:outline-none focus:ring-2 focus:ring-[#153D32]"
                  />
                </div>
              </div>
            </div>

            <div className="pt-4 flex items-center justify-between">
              <button
                type="button"
                onClick={handleBack}
                className="btn-civic-secondary text-xs !py-2.5 !px-4"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button
                type="button"
                onClick={handleNext}
                className="btn-civic-primary text-xs !py-2.5 !px-5"
              >
                <span>Continue to Evidence</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 4: PHOTO & EVIDENCE UPLOAD ================= */}
        {step === 4 && (
          <div className="space-y-4">
            <div className="space-y-1">
              <h2 className="text-base font-heading font-bold text-[#17221F]">
                Attach Photographs or Documents (Optional)
              </h2>
              <p className="text-xs text-[#69736D]">
                Adding photos of the damaged road, contaminated water, or broken pipe speeds up physical verification.
              </p>
            </div>

            <div className="pt-2">
              <label className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-[#E5E7DF] hover:border-[#153D32] rounded-2xl bg-[#F7F6F0] cursor-pointer transition">
                <input
                  type="file"
                  accept="image/*,.pdf,.doc,.docx"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <Camera className="w-8 h-8 text-[#153D32] mb-2" />
                <span className="text-xs font-bold text-[#17221F]">Click to upload photograph or document</span>
                <span className="text-[11px] text-[#69736D] mt-0.5">PNG, JPG, PDF up to 10MB</span>
              </label>

              {file && (
                <div className="mt-3 p-3 rounded-xl bg-[#EFF5EF] border border-[#DDE8DD] flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 truncate">
                    <FileText className="w-4 h-4 text-[#153D32]" />
                    <span className="font-semibold text-[#17221F] truncate">{file.name}</span>
                    <span className="text-[10px] text-[#69736D]">({Math.round(file.size / 1024)} KB)</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => { setFile(null); setFilePreview(null); }}
                    className="text-xs text-[#991B1B] font-bold hover:underline"
                  >
                    Remove
                  </button>
                </div>
              )}

              {filePreview && (
                <div className="mt-3">
                  <span className="text-[11px] text-[#69736D] block mb-1">Preview:</span>
                  <img src={filePreview} alt="Upload preview" className="max-h-48 rounded-xl object-cover border border-[#E5E7DF]" />
                </div>
              )}
            </div>

            <div className="pt-4 flex items-center justify-between">
              <button
                type="button"
                onClick={handleBack}
                className="btn-civic-secondary text-xs !py-2.5 !px-4"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button
                type="button"
                onClick={handleNext}
                className="btn-civic-primary text-xs !py-2.5 !px-5"
              >
                <span>Continue to Review</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 5: FINAL REVIEW ================= */}
        {step === 5 && (
          <div className="space-y-5">
            <div className="space-y-1">
              <h2 className="text-base font-heading font-bold text-[#17221F]">
                Review Your Grievance Submission
              </h2>
              <p className="text-xs text-[#69736D]">
                Please verify that the details below are accurate before lodging onto the public ledger.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[#F7F6F0] border border-[#E5E7DF] space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-2 pb-2 border-b border-[#E5E7DF]">
                <div>
                  <span className="text-[10px] uppercase font-bold text-[#69736D] block">Category</span>
                  <span className="font-bold text-[#153D32]">{category}</span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-[#69736D] block">Priority</span>
                  <span className="font-bold text-[#17221F]">{priority}</span>
                </div>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-[#69736D] block">Title</span>
                <span className="font-bold text-[#17221F]">{title}</span>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-[#69736D] block">Detailed Description</span>
                <p className="text-[#404B46] leading-relaxed mt-0.5">{description}</p>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-[#69736D] block">Location</span>
                <span className="text-[#17221F]">{ward}, {location}</span>
              </div>

              {file && (
                <div>
                  <span className="text-[10px] uppercase font-bold text-[#69736D] block">Attachment</span>
                  <span className="text-[#153D32] font-semibold">{file.name}</span>
                </div>
              )}
            </div>

            <div className="pt-4 flex items-center justify-between">
              <button
                type="button"
                onClick={handleBack}
                disabled={loading}
                className="btn-civic-secondary text-xs !py-2.5 !px-4"
              >
                <ArrowLeft className="w-4 h-4" /> Edit Details
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="btn-civic-primary text-xs !py-3 !px-6 font-bold shadow-md shadow-[#153D32]/20"
              >
                {loading ? 'Submitting to Panchayat...' : 'Confirm & Lodge Grievance'}
              </button>
            </div>
          </div>
        )}

        {/* ================= STEP 6: CONFIRMATION SCREEN ================= */}
        {step === 6 && submittedComplaint && (
          <div className="text-center py-6 space-y-6 animate-civic-fade">
            
            <div className="w-16 h-16 rounded-full bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0] flex items-center justify-center mx-auto shadow-md">
              <CheckCircle2 className="w-8 h-8 text-[#065F46]" />
            </div>

            <div className="space-y-1">
              <h2 className="text-2xl font-heading font-extrabold text-[#17221F]">
                Grievance Lodged Successfully!
              </h2>
              <p className="text-xs text-[#69736D]">
                Your complaint has been logged in the Gram Panchayat register and assigned to the triage queue.
              </p>
            </div>

            {/* Complaint Number Banner with Copy */}
            <div className="p-4 rounded-2xl bg-[#F7F6F0] border border-[#E5E7DF] max-w-sm mx-auto space-y-2">
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#69736D] block">
                Official Tracking ID
              </span>
              <div className="flex items-center justify-center gap-2">
                <span className="text-xl font-heading font-extrabold font-mono text-[#153D32]">
                  {submittedComplaint.complaint_number}
                </span>
                <button
                  type="button"
                  onClick={() => copyToClipboard(submittedComplaint.complaint_number)}
                  className="p-1.5 rounded-md hover:bg-[#FFFFFF] text-[#69736D] hover:text-[#17221F] border border-transparent hover:border-[#E5E7DF] transition"
                  title="Copy Tracking ID"
                >
                  {copied ? <Check className="w-4 h-4 text-[#065F46]" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              <span className="text-[11px] text-[#69736D] block">
                Save this ID to track updates or ask the AI Assistant.
              </span>
            </div>

            {/* Next Steps Guidance */}
            <div className="p-4 rounded-xl bg-[#EFF5EF] border border-[#DDE8DD] text-xs text-left space-y-2 text-[#153D32] max-w-md mx-auto">
              <span className="font-bold block">What happens next:</span>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-[#404B46]">
                <li>Panchayat Staff will acknowledge and verify your ward details within 24 hours.</li>
                <li>The complaint will be routed to the appropriate department inspection officer.</li>
                <li>You can consult the AI Assistant anytime to check the latest field inspector remarks.</li>
              </ul>
            </div>

            {/* CTAs */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Link
                to={`/track?id=${submittedComplaint.complaint_number}`}
                className="btn-civic-primary text-xs !py-2.5 !px-5"
              >
                <Search className="w-4 h-4" /> Track Complaint Progress
              </Link>
              <Link
                to="/dashboard"
                className="btn-civic-secondary text-xs !py-2.5 !px-5"
              >
                Go to Citizen Dashboard
              </Link>
            </div>

          </div>
        )}

      </div>

    </div>
  );
};

export default SubmitComplaintPage;
