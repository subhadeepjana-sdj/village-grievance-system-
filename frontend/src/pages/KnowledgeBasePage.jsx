import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { 
  FileText, Upload, Database, PlusCircle, CheckCircle2, 
  AlertCircle, Search, ExternalLink, ShieldCheck, Filter, Download
} from 'lucide-react';

const KnowledgeBasePage = () => {
  const { user } = useAuth();
  const isStaffOrAdmin = ['ADMIN', 'PANCHAYAT_STAFF', 'RESEARCHER'].includes(user?.role);

  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDept, setSelectedDept] = useState('ALL');

  // Upload Form State
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('Village Water Department');
  const [category, setCategory] = useState('Water Supply');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchDocuments = async () => {
    try {
      const res = await api.get('/documents');
      setDocuments(res.data);
    } catch (err) {
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setMsg('');
    setErrorMsg('');

    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('department', department);
      formData.append('category', category);
      formData.append('file', file);

      await api.post('/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setMsg('Document uploaded & Qdrant vector index created successfully!');
      setTitle('');
      setFile(null);
      setShowUploadModal(false);
      fetchDocuments();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (doc.department && doc.department.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesDept = selectedDept === 'ALL' || doc.department === selectedDept;
    return matchesSearch && matchesDept;
  });

  const departments = ['ALL', ...new Set(documents.map(d => d.department).filter(Boolean))];

  return (
    <div className="space-y-6 p-4 sm:p-8 max-w-7xl mx-auto">
      
      {/* Editorial Header */}
      <div className="civic-card p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 border-l-4 border-l-[#153D32]">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#DDE8DD] text-[#153D32] text-xs font-bold uppercase tracking-wider">
            <Database className="w-3.5 h-3.5" /> Qdrant Grounding Corpus
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#17221F] tracking-tight">
            Gram Panchayat Knowledge Base
          </h1>
          <p className="text-sm text-[#69736D] max-w-2xl leading-relaxed">
            Official service charters, scheme rules, and verified policy documents indexed into dense vector embeddings for deterministic LLM hallucination prevention.
          </p>
        </div>

        {isStaffOrAdmin && (
          <button
            onClick={() => setShowUploadModal(true)}
            className="btn-civic-primary self-start md:self-auto flex items-center gap-2"
          >
            <PlusCircle className="w-4 h-4 text-[#D7F36A]" /> Upload & Index Document
          </button>
        )}
      </div>

      {msg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center gap-2.5">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{msg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center gap-2.5">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Search & Filter Toolbar */}
      <div className="civic-card p-4 sm:p-5 flex flex-col sm:flex-row gap-4 justify-between items-stretch sm:items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-[#69736D] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search charters, schemes, guidelines..."
            className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-[#E5E7DF] rounded-xl text-[#17221F] placeholder-[#69736D] focus:outline-none focus:border-[#153D32]"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
          <span className="text-xs font-bold text-[#69736D] uppercase flex items-center gap-1 shrink-0">
            <Filter className="w-3.5 h-3.5" /> Department:
          </span>
          {departments.map((dept) => (
            <button
              key={dept}
              onClick={() => setSelectedDept(dept)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                selectedDept === dept
                  ? 'bg-[#153D32] text-white shadow-sm'
                  : 'bg-white text-[#69736D] border border-[#E5E7DF] hover:bg-[#F7F6F0]'
              }`}
            >
              {dept === 'ALL' ? 'All Departments' : dept}
            </button>
          ))}
        </div>
      </div>

      {/* Document Grid */}
      {loading ? (
        <div className="civic-card p-12 text-center text-[#69736D] text-sm animate-pulse">
          Loading knowledge base documents and vector representations...
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="civic-card p-12 text-center space-y-3">
          <FileText className="w-10 h-10 text-[#69736D] mx-auto opacity-50" />
          <h3 className="font-bold text-[#17221F] text-base">No matching documents found</h3>
          <p className="text-xs text-[#69736D] max-w-md mx-auto">
            Try adjusting your search keywords or filter to find specific official village charters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredDocs.map((doc) => (
            <div key={doc.id} className="civic-card p-6 flex flex-col justify-between space-y-4 hover:shadow-md transition">
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[11px] font-bold px-2.5 py-1 rounded-md bg-[#DDE8DD] text-[#153D32]">
                    {doc.document_type || 'OFFICIAL_RECORD'}
                  </span>
                  <span className="text-xs font-mono font-semibold text-[#69736D]">
                    v{doc.version || '1.0'}
                  </span>
                </div>
                
                <h3 className="font-bold text-[#17221F] text-base leading-snug line-clamp-2">
                  {doc.title}
                </h3>
                
                <div className="text-xs text-[#69736D] space-y-1.5 pt-1">
                  <div className="flex items-center justify-between">
                    <span>Department:</span>
                    <span className="text-[#17221F] font-medium">{doc.department || 'Village Administration'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Uploaded By:</span>
                    <span className="text-[#17221F] font-medium">{doc.uploaded_by || 'Staff'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Indexing Date:</span>
                    <span className="text-[#17221F] font-medium">{new Date(doc.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-[#E5E7DF] flex items-center justify-between text-xs">
                <span className="text-[#15803D] font-bold flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#15803D]" /> Vector Grounded
                </span>
                <a
                  href={`/uploads/${doc.file_path ? doc.file_path.replace('uploads/', '') : ''}`}
                  target="_blank"
                  rel="noreferrer"
                  className="font-bold text-[#153D32] hover:text-[#17221F] inline-flex items-center gap-1 transition"
                >
                  View Source <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="relative w-full max-w-lg civic-card p-6 sm:p-8 space-y-5 bg-[#F7F6F0]">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-[#17221F] flex items-center gap-2">
                <Upload className="w-5 h-5 text-[#153D32]" /> Upload & Index Knowledge Document
              </h3>
              <button 
                onClick={() => setShowUploadModal(false)}
                className="text-[#69736D] hover:text-[#17221F] text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
              <div>
                <label className="font-bold text-[#17221F] block mb-1">Document Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  placeholder="e.g. Village Sanitation Guidelines 2026"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E5E7DF] text-[#17221F] focus:outline-none focus:border-[#153D32]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-[#17221F] block mb-1">Department</label>
                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E5E7DF] text-[#17221F] focus:outline-none focus:border-[#153D32]"
                  >
                    <option value="Village Water Department">Village Water Department</option>
                    <option value="Roads & Public Works Department">Roads & Public Works Department</option>
                    <option value="Rural Sanitation Department">Rural Sanitation Department</option>
                    <option value="Electricity & Power Supply Board">Electricity & Power Supply Board</option>
                    <option value="Village Welfare & Schemes Department">Village Welfare & Schemes Department</option>
                  </select>
                </div>

                <div>
                  <label className="font-bold text-[#17221F] block mb-1">Category</label>
                  <input
                    type="text"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    placeholder="Water Supply"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#E5E7DF] text-[#17221F] focus:outline-none focus:border-[#153D32]"
                  />
                </div>
              </div>

              <div>
                <label className="font-bold text-[#17221F] block mb-1">Select File (PDF, DOCX, TXT)</label>
                <input
                  type="file"
                  onChange={(e) => setFile(e.target.files[0])}
                  required
                  className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#E5E7DF] text-[#17221F]"
                />
              </div>

              <div className="pt-3 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2.5 rounded-xl bg-white border border-[#E5E7DF] text-[#69736D] font-bold hover:bg-[#F7F6F0]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="btn-civic-primary px-6 py-2.5 disabled:opacity-50"
                >
                  {uploading ? 'Processing & Vectorizing...' : 'Upload & Index'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default KnowledgeBasePage;
