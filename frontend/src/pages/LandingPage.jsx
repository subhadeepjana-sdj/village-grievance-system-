import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Building2, ShieldCheck, Bot, FileText, ArrowRight, CheckCircle2,
  AlertTriangle, Sparkles, Search, PlusCircle, Layers, Database,
  Clock, Eye, FileCheck2, Scale, HelpCircle, Smartphone, Users,
  Check, ChevronRight, ShieldAlert, BarChart3
} from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import GISEmblem from "../components/GISEmblem";

const LandingPage = () => {
  const [activeTab, setActiveTab] = useState("comparison");

  return (
    <div style={{ background: "#F8FAFC", minHeight: "100vh" }}>

      {/* ═══════════════════════════════════════════
          HERO SECTION
      ═══════════════════════════════════════════ */}
      <section style={{ background: "#F8FAFC", paddingTop: "56px", paddingBottom: "72px" }}>
        <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "0 32px" }}>
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "64px",
            alignItems: "center",
          }}
            className="hero-grid"
          >

            {/* ── LEFT: Typography + CTAs ── */}
            <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

              {/* Badge */}
              <div style={{
                display: "inline-flex", alignItems: "center", gap: "10px",
                padding: "6px 14px", borderRadius: "9999px",
                background: "#E8F0FE", border: "1px solid #BFDBFE",
                width: "fit-content",
              }}>
                <GISEmblem size={18} />
                <span style={{ fontSize: "10px", fontWeight: 800, color: "#0047BA", letterSpacing: "1.2px", textTransform: "uppercase" }}>
                  GIS CIVIC INTELLIGENCE
                </span>
                <span style={{ color: "#94A3B8" }}>•</span>
                <span style={{ fontSize: "11px", fontWeight: 600, color: "#0047BA" }}>
                  Hallucination-Protected RAG
                </span>
              </div>

              {/* Headline */}
              <h1 style={{
                fontSize: "clamp(32px, 4vw, 52px)", fontWeight: 800,
                color: "#0F172A", lineHeight: 1.08, letterSpacing: "-0.03em",
                margin: 0, fontFamily: "'Plus Jakarta Sans', sans-serif",
              }}>
                Local problems deserve answers{" "}
                <em style={{
                  color: "#0047BA", fontStyle: "italic", fontWeight: 400,
                  textDecoration: "underline", textDecorationColor: "#00A3E0",
                  textDecorationThickness: "3px", textUnderlineOffset: "6px",
                }}>
                  backed by evidence.
                </em>
              </h1>

              {/* Sub-text */}
              <p style={{ fontSize: "16px", color: "#475569", lineHeight: 1.7, margin: 0, maxWidth: "520px" }}>
                A transparent civic redressal platform for rural Gram Panchayats. Citizens submit grievances, track live status updates, and ask questions with AI answers strictly validated against official village records.
              </p>

              {/* CTAs */}
              <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", alignItems: "center" }}>
                <Link to="/submit" className="btn-gis-primary" style={{ fontSize: "14px", padding: "12px 24px" }}>
                  <PlusCircle size={16} />
                  <span>Submit a Grievance</span>
                  <ArrowRight size={16} />
                </Link>
                <Link to="/ai-assistant" className="btn-gis-secondary" style={{ fontSize: "14px", padding: "12px 24px" }}>
                  <Bot size={16} />
                  <span>Explore AI Assistant</span>
                </Link>
              </div>

              {/* Trust checkmarks */}
              <div style={{ display: "flex", gap: "24px", flexWrap: "wrap" }}>
                {["Evidence-backed answers", "Transparent complaint tracking", "Zero ungrounded hallucinations"].map(text => (
                  <div key={text} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <CheckCircle2 size={15} style={{ color: "#16A34A", flexShrink: 0 }} />
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "#475569" }}>{text}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* ── RIGHT: Dashboard Preview Cards ── */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>

              {/* Grievance card */}
              <div className="civic-card" style={{ padding: "20px" }}>
                <div style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  paddingBottom: "12px", borderBottom: "1px solid #E5E7DF", marginBottom: "12px",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span style={{
                      fontFamily: "monospace", fontSize: "11px", fontWeight: 700,
                      background: "#F7F6F0", border: "1px solid #E5E7DF", color: "#153D32",
                      padding: "2px 8px", borderRadius: "6px",
                    }}>
                      GRV-YYYY-XXXXXX
                    </span>
                    <span style={{ fontSize: "11px", color: "#69736D" }}>Workflow Illustration</span>
                  </div>
                  <StatusBadge status="UNDER_REVIEW" />
                </div>
                <h3 style={{ margin: "0 0 6px", fontSize: "13px", fontWeight: 700, color: "#17221F" }}>
                  Citizen Grievance Workflow
                </h3>
                <p style={{ margin: "0 0 10px", fontSize: "12px", color: "#404B46", lineHeight: 1.5 }}>
                  Submissions created in the User portal are persisted to MongoDB and appear immediately in the Administrator queue with full audit history.
                </p>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#69736D" }}>
                  <span>Routing: <strong>Department Assignment</strong></span>
                  <span>Storage: <strong>MongoDB + SQL Sync</strong></span>
                </div>
              </div>

              {/* RAG bridge pill */}
              <div style={{ display: "flex", justifyContent: "center" }}>
                <div style={{
                  display: "inline-flex", alignItems: "center", gap: "8px",
                  padding: "5px 14px", borderRadius: "9999px",
                  background: "#EFF5EF", border: "1px solid #DDE8DD",
                  fontSize: "11px", fontWeight: 600, color: "#153D32",
                }}>
                  <Database size={13} style={{ color: "#15803D" }} />
                  Hybrid RAG Grounding Citation
                  <span style={{ fontFamily: "monospace", fontSize: "10px", color: "#69736D" }}>(Similarity 0.94)</span>
                </div>
              </div>

              {/* AI response card */}
              <div className="civic-card" style={{ padding: "20px", borderColor: "rgba(21,61,50,0.2)", borderWidth: "2px" }}>
                <div style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  paddingBottom: "12px", borderBottom: "1px solid #E5E7DF", marginBottom: "12px",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <div style={{
                      width: "24px", height: "24px", borderRadius: "6px",
                      background: "#153D32", display: "flex", alignItems: "center", justifyContent: "center",
                    }}>
                      <Sparkles size={13} style={{ color: "#D7F36A" }} />
                    </div>
                    <span style={{ fontSize: "12px", fontWeight: 700, color: "#17221F" }}>Civic AI Assistant</span>
                  </div>
                  <div style={{
                    display: "inline-flex", alignItems: "center", gap: "5px",
                    padding: "3px 10px", borderRadius: "9999px",
                    background: "#ECFDF5", border: "1px solid #A7F3D0",
                    fontSize: "11px", fontWeight: 700, color: "#065F46",
                  }}>
                    <ShieldCheck size={13} /> ✓ Evidence Verified
                  </div>
                </div>
                <div style={{ fontSize: "11px", color: "#69736D", marginBottom: "8px" }}>
                  Q: <em>"Who is handling my submitted complaint?"</em>
                </div>
                <p style={{
                  fontSize: "12px", color: "#17221F", lineHeight: 1.6, margin: "0 0 10px",
                  background: "#F7F6F0", padding: "10px 12px", borderRadius: "8px", border: "1px solid #E5E7DF",
                }}>
                  Every answer is grounded exclusively in live grievance records and uploaded Panchayat knowledge documents, or safely abstains if no record exists.
                </p>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#69736D" }}>
                  <span style={{ fontFamily: "monospace" }}>Mode: <strong style={{ color: "#065F46" }}>Evidence-Gated</strong></span>
                  <span style={{ color: "#153D32", fontWeight: 600, display: "flex", alignItems: "center", gap: "4px" }}>
                    <FileCheck2 size={13} /> Zero Unverified Claims
                  </span>
                </div>
              </div>

            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          TRUST PILLARS STRIP
      ═══════════════════════════════════════════ */}
      <section style={{ background: "#FFFFFF", borderTop: "1px solid #E2E8F0", borderBottom: "1px solid #E2E8F0", padding: "32px 0" }}>
        <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "0 32px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0" }}>
            {[
              { Icon: ShieldCheck, title: "Evidence-Grounded", desc: "Responses strictly bound to official Panchayat records" },
              { Icon: Search,      title: "Transparent Tracking", desc: "Complete milestone audit trails from submission to resolution" },
              { Icon: FileCheck2,  title: "Source-Linked Citations", desc: "Every factual assertion cites exact document chunks" },
              { Icon: Scale,       title: "Human-Reviewed", desc: "Dedicated triage by Panchayat Staff and Department Officers" },
            ].map(({ Icon, title, desc }, i) => (
              <div key={title} style={{
                padding: "20px 24px", textAlign: "center",
                borderRight: i < 3 ? "1px solid #E2E8F0" : "none",
              }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", marginBottom: "6px" }}>
                  <Icon size={18} style={{ color: "#15803D" }} />
                  <span style={{ fontSize: "13px", fontWeight: 700, color: "#153D32", fontFamily: "'Plus Jakarta Sans',sans-serif" }}>{title}</span>
                </div>
                <p style={{ fontSize: "12px", color: "#69736D", margin: 0, lineHeight: 1.5 }}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          HOW IT WORKS – 4 STEP GRID
      ═══════════════════════════════════════════ */}
      <section id="how-it-works" style={{ padding: "80px 0", background: "#F8FAFC" }}>
        <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "0 32px" }}>

          {/* Section header */}
          <div style={{ textAlign: "center", marginBottom: "48px" }}>
            <span style={{
              display: "inline-block", fontSize: "11px", fontWeight: 800, letterSpacing: "1.5px",
              textTransform: "uppercase", color: "#153D32", background: "#EFF5EF",
              border: "1px solid #DDE8DD", padding: "4px 14px", borderRadius: "9999px", marginBottom: "12px",
            }}>
              Transparent Governance Flow
            </span>
            <h2 style={{ fontSize: "30px", fontWeight: 800, color: "#17221F", margin: "0 0 12px", fontFamily: "'Plus Jakarta Sans',sans-serif" }}>
              How Civic Intelligence Works
            </h2>
            <p style={{ fontSize: "14px", color: "#404B46", maxWidth: "480px", margin: "0 auto", lineHeight: 1.6 }}>
              From the moment a village issue is reported to when an evidence-verified answer is delivered.
            </p>
          </div>

          {/* 4-column step cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "24px" }}>
            {[
              { num: "01", bg: "#153D32", numColor: "#D7F36A", title: "Submit a Grievance", desc: "Citizens lodge complaints online with category, location, and photos. A unique tracking ID (GRV-YYYY-XXXXXX) is issued instantly.", tag: "Photo & document attachments" },
              { num: "02", bg: "#EFF5EF", numColor: "#153D32", title: "Retrieve Verified Data", desc: "Hybrid search queries live PostgreSQL database records alongside Qdrant vector knowledge chunks.", tag: "Postgres + Qdrant hybrid retrieval" },
              { num: "03", bg: "#EFF5EF", numColor: "#153D32", title: "Verify Claims via NLI", desc: "Candidate text is split into atomic claims. Natural Language Inference checks each claim against retrieved evidence.", tag: "Contradiction detection engine" },
              { num: "04", bg: "#D7F36A", numColor: "#17221F", title: "Grounded Output or Abstain", desc: "If supported, answer shown with source badges. If contradicted, corrected. If evidence insufficient, system safely abstains.", tag: "Honest & transparent outputs" },
            ].map(({ num, bg, numColor, title, desc, tag }) => (
              <div key={num} className="civic-card" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "12px" }}>
                <div style={{
                  width: "40px", height: "40px", borderRadius: "10px",
                  background: bg, color: numColor,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "13px", fontWeight: 800, fontFamily: "'Plus Jakarta Sans',sans-serif",
                  border: bg === "#EFF5EF" ? "1px solid #DDE8DD" : "none",
                }}>
                  {num}
                </div>
                <h3 style={{ fontSize: "14px", fontWeight: 700, color: "#17221F", margin: 0 }}>{title}</h3>
                <p style={{ fontSize: "12px", color: "#69736D", lineHeight: 1.6, margin: 0, flex: 1 }}>{desc}</p>
                <span style={{
                  display: "inline-block", fontSize: "11px", fontWeight: 600, color: "#153D32",
                  background: "#EFF5EF", border: "1px solid #DDE8DD",
                  padding: "3px 10px", borderRadius: "9999px",
                }}>
                  {tag}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          HALLUCINATION DETECTION SHOWCASE
      ═══════════════════════════════════════════ */}
      <section id="verification-showcase" className="civic-panel-forest" style={{ padding: "72px 0", margin: "0" }}>
        <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "0 32px" }}>

          {/* Section header */}
          <div style={{ marginBottom: "40px" }}>
            <div style={{
              display: "inline-flex", alignItems: "center", gap: "6px",
              padding: "4px 12px", borderRadius: "9999px", background: "#D7F36A", marginBottom: "14px",
            }}>
              <ShieldCheck size={14} style={{ color: "#153D32" }} />
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#153D32" }}>Interactive Research Showcase</span>
            </div>
            <h2 style={{ fontSize: "clamp(24px,3vw,38px)", fontWeight: 800, color: "#FFFFFF", margin: "0 0 10px", lineHeight: 1.15, fontFamily: "'Plus Jakarta Sans',sans-serif" }}>
              How Hallucination Detection Intercepts Errors
            </h2>
            <p style={{ fontSize: "14px", color: "#DDE8DD", maxWidth: "580px", lineHeight: 1.6 }}>
              Witness how raw LLM claims can fabricate departments or statuses, and how our NLI pipeline automatically catches and corrects inaccuracies before citizens see them.
            </p>
          </div>

          {/* White content card */}
          <div style={{ background: "#FFFFFF", borderRadius: "16px", padding: "32px", boxShadow: "0 20px 60px rgba(0,0,0,0.25)" }}>

            {/* Query bar */}
            <div style={{
              display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px",
              padding: "16px", borderRadius: "10px", background: "#F7F6F0", border: "1px solid #E5E7DF", marginBottom: "24px",
            }}>
              <div>
                <div style={{ fontSize: "10px", fontWeight: 700, color: "#69736D", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "2px" }}>
                  Citizen Question
                </div>
                <div style={{ fontSize: "14px", fontWeight: 700, color: "#17221F" }}>
                  "Who is handling complaint GRV-1024?"
                </div>
              </div>
              <div style={{
                display: "flex", alignItems: "center", gap: "6px",
                padding: "6px 12px", borderRadius: "8px", background: "#EFF5EF", border: "1px solid #DDE8DD",
                fontSize: "12px", fontWeight: 600, color: "#153D32",
              }}>
                <Database size={13} />
                Retrieved: Dept = Water, Status = Under Review
              </div>
            </div>

            {/* Tabs */}
            <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid #E5E7DF", paddingBottom: "12px", marginBottom: "24px" }}>
              {[
                { key: "comparison", label: "Side-by-Side Comparison" },
                { key: "candidate",  label: "Raw LLM Candidate (Hallucinated)" },
                { key: "corrected",  label: "Verified Output (Grounded)" },
              ].map(({ key, label }) => (
                <button key={key} onClick={() => setActiveTab(key)} style={{
                  padding: "6px 14px", borderRadius: "8px", cursor: "pointer",
                  fontSize: "12px", fontWeight: 700, transition: "all 0.15s",
                  background: activeTab === key ? (key === "candidate" ? "#FEF2F2" : key === "corrected" ? "#ECFDF5" : "#153D32") : "transparent",
                  color: activeTab === key ? (key === "candidate" ? "#991B1B" : key === "corrected" ? "#065F46" : "#FFFFFF") : "#69736D",
                  border: activeTab === key && key !== "comparison" ? `1px solid ${key === "candidate" ? "#FECACA" : "#A7F3D0"}` : "1px solid transparent",
                }}>
                  {label}
                </button>
              ))}
            </div>

            {/* Comparison tab */}
            {activeTab === "comparison" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

                {/* 2-column side by side */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>

                  {/* Unverified */}
                  <div style={{ padding: "16px", borderRadius: "12px", background: "#FEF2F2", border: "2px solid #FECACA" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                      <span style={{ fontSize: "12px", fontWeight: 700, color: "#991B1B" }}>Raw LLM Generation</span>
                      <span style={{ fontSize: "10px", fontWeight: 800, color: "#991B1B", background: "#FEE2E2", padding: "2px 8px", borderRadius: "4px" }}>UNVERIFIED</span>
                    </div>
                    <p style={{ fontSize: "12px", color: "#7F1D1D", lineHeight: 1.6, margin: "0 0 10px" }}>
                      "Your complaint is being handled by the{" "}
                      <mark style={{ background: "#FECACA", color: "#991B1B", fontWeight: 700, padding: "1px 4px", borderRadius: "3px" }}>Road Department</mark>
                      {" "}and is currently pending contractor assignment."
                    </p>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", color: "#991B1B", fontWeight: 600 }}>
                      <AlertTriangle size={13} />
                      Contradicts complaint fact record
                    </div>
                  </div>

                  {/* Verified */}
                  <div style={{ padding: "16px", borderRadius: "12px", background: "#ECFDF5", border: "2px solid #A7F3D0" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                      <span style={{ fontSize: "12px", fontWeight: 700, color: "#065F46" }}>Verified Corrected Output</span>
                      <span style={{ fontSize: "10px", fontWeight: 800, color: "#065F46", background: "#D1FAE5", padding: "2px 8px", borderRadius: "4px" }}>CORRECTED & GROUNDED</span>
                    </div>
                    <p style={{ fontSize: "12px", color: "#064E3B", lineHeight: 1.6, margin: "0 0 10px" }}>
                      "Your complaint is under review by the{" "}
                      <strong style={{ textDecoration: "underline", textDecorationColor: "#15803D" }}>Village Water Department</strong>
                      . An inspection team was dispatched to Ward 4."
                    </p>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", color: "#065F46", fontWeight: 600 }}>
                      <CheckCircle2 size={13} />
                      NLI Entailment: 96% Faithfulness
                    </div>
                  </div>
                </div>

                {/* NLI Table */}
                <div style={{ border: "1px solid #E5E7DF", borderRadius: "12px", overflow: "hidden" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                    <thead>
                      <tr style={{ background: "#F1F5F9", borderBottom: "1px solid #E5E7DF" }}>
                        {["Generated Claim", "Retrieved Evidence", "Verification Result", "Pipeline Decision"].map(h => (
                          <th key={h} style={{ padding: "10px 16px", textAlign: "left", fontSize: "10px", fontWeight: 700, color: "#64748B", textTransform: "uppercase", letterSpacing: "0.8px" }}>
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ borderBottom: "1px solid #F1F5F9" }}>
                        <td style={{ padding: "12px 16px", color: "#991B1B", fontWeight: 600, textDecoration: "line-through" }}>Road Department (Handling)</td>
                        <td style={{ padding: "12px 16px", color: "#065F46", fontWeight: 600 }}>Village Water Department (Status: Under Review)</td>
                        <td style={{ padding: "12px 16px" }}>
                          <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", padding: "2px 8px", borderRadius: "6px", background: "#FEF2F2", color: "#991B1B", border: "1px solid #FECACA", fontSize: "11px", fontWeight: 700 }}>
                            <AlertTriangle size={11} /> Contradicted
                          </span>
                        </td>
                        <td style={{ padding: "12px 16px" }}>
                          <span style={{ padding: "2px 8px", borderRadius: "6px", background: "#EFF5EF", color: "#153D32", fontSize: "11px", fontWeight: 700 }}>
                            REGENERATE / CORRECT
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === "candidate" && (
              <div style={{ padding: "20px", borderRadius: "12px", background: "#FEF2F2", border: "1px solid #FECACA" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", fontWeight: 700, color: "#991B1B", marginBottom: "12px" }}>
                  <AlertTriangle size={16} /> Raw Unconstrained LLM Answer (Baseline)
                </div>
                <p style={{ fontSize: "14px", color: "#7F1D1D", lineHeight: 1.7, marginBottom: "12px" }}>
                  "Your complaint is being handled by the Road Department and is currently pending contractor assignment."
                </p>
                <div style={{ padding: "12px", borderRadius: "8px", background: "#FFFFFF", border: "1px solid #FECACA", fontSize: "12px", color: "#991B1B", lineHeight: 1.6 }}>
                  <strong>Why this is dangerous in public services:</strong> Without verification, citizens receive misleading information regarding who to contact and the real operational status.
                </div>
              </div>
            )}

            {activeTab === "corrected" && (
              <div style={{ padding: "20px", borderRadius: "12px", background: "#ECFDF5", border: "1px solid #A7F3D0" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", fontWeight: 700, color: "#065F46", marginBottom: "12px" }}>
                  <CheckCircle2 size={16} /> Evidence-Grounded Output Presented to Citizen
                </div>
                <p style={{ fontSize: "14px", color: "#064E3B", lineHeight: 1.7, marginBottom: "12px" }}>
                  "Your complaint GRV-1024 is currently under review by the Village Water Department. An inspection team has been dispatched."
                </p>
                <div style={{ padding: "12px", borderRadius: "8px", background: "#FFFFFF", border: "1px solid #A7F3D0", fontSize: "12px", color: "#065F46", lineHeight: 1.6 }}>
                  <strong>Research contribution:</strong> Grounded claim extraction ensures all stated departments and statuses match the authoritative database before presentation.
                </div>
              </div>
            )}

          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          PLATFORM CAPABILITIES
      ═══════════════════════════════════════════ */}
      <section style={{ padding: "80px 0", background: "#F8FAFC" }}>
        <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "0 32px" }}>

          {/* Header */}
          <div style={{ textAlign: "center", marginBottom: "48px" }}>
            <span style={{
              display: "inline-block", fontSize: "11px", fontWeight: 800, letterSpacing: "1.5px",
              textTransform: "uppercase", color: "#153D32", background: "#EFF5EF",
              border: "1px solid #DDE8DD", padding: "4px 14px", borderRadius: "9999px", marginBottom: "12px",
            }}>
              Platform Capabilities
            </span>
            <h2 style={{ fontSize: "30px", fontWeight: 800, color: "#17221F", margin: "0 0 12px", fontFamily: "'Plus Jakarta Sans',sans-serif" }}>
              Built for Citizens, Staff & Researchers
            </h2>
            <p style={{ fontSize: "14px", color: "#404B46", maxWidth: "480px", margin: "0 auto", lineHeight: 1.6 }}>
              Every layer is designed for accountability, granular verification, and rural accessibility.
            </p>
          </div>

          {/* 3-col bento grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "24px" }}>

            {/* Submit & Track – spans 2 */}
            <div className="civic-card" style={{ padding: "32px", gridColumn: "span 2" }}>
              <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: "#EFF5EF", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "16px" }}>
                <PlusCircle size={20} style={{ color: "#153D32" }} />
              </div>
              <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#17221F", margin: "0 0 10px", fontFamily: "'Plus Jakarta Sans',sans-serif" }}>
                Submit & Track Civic Grievances
              </h3>
              <p style={{ fontSize: "14px", color: "#404B46", lineHeight: 1.6, margin: "0 0 16px" }}>
                Step-by-step grievance submission wizard supporting village wards, photo uploads, GPS landmarks, and milestone progress tracking with full status change history.
              </p>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {["Ward-wise Categorization", "Document & Photo Attachment", "Public Milestone Tracking"].map(tag => (
                  <span key={tag} style={{
                    display: "inline-flex", padding: "4px 12px", borderRadius: "9999px",
                    background: "#F7F6F0", border: "1px solid #E5E7DF",
                    fontSize: "11px", fontWeight: 600, color: "#153D32",
                  }}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Evidence-Grounded AI */}
            <div className="civic-card" style={{ padding: "32px" }}>
              <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: "#D7F36A", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "16px" }}>
                <Bot size={20} style={{ color: "#17221F" }} />
              </div>
              <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#17221F", margin: "0 0 10px", fontFamily: "'Plus Jakarta Sans',sans-serif" }}>
                Evidence-Grounded Assistant
              </h3>
              <p style={{ fontSize: "14px", color: "#404B46", lineHeight: 1.6, margin: "0 0 16px" }}>
                Natural language answers that cite official Gram Panchayat bylaws, scheme rules, and live complaint statuses.
              </p>
              <Link to="/ai-assistant" style={{
                display: "inline-flex", alignItems: "center", gap: "4px",
                fontSize: "12px", fontWeight: 700, color: "#153D32", textDecoration: "none",
              }}>
                Try asking a question <ChevronRight size={14} />
              </Link>
            </div>

            {/* Inspectable Citations */}
            <div className="civic-card" style={{ padding: "32px" }}>
              <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: "#EFF5EF", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "16px" }}>
                <FileCheck2 size={20} style={{ color: "#153D32" }} />
              </div>
              <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#17221F", margin: "0 0 10px", fontFamily: "'Plus Jakarta Sans',sans-serif" }}>
                Inspectable Citations
              </h3>
              <p style={{ fontSize: "14px", color: "#404B46", lineHeight: 1.6 }}>
                Every factual assertion includes clickable evidence chips showing similarity scores and exact text excerpts from the grounding corpus.
              </p>
            </div>

            {/* Panchayat Workspace – spans 2 */}
            <div className="civic-card" style={{ padding: "32px", gridColumn: "span 2" }}>
              <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: "#153D32", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "16px" }}>
                <Building2 size={20} style={{ color: "#D7F36A" }} />
              </div>
              <h3 style={{ fontSize: "18px", fontWeight: 700, color: "#17221F", margin: "0 0 10px", fontFamily: "'Plus Jakarta Sans',sans-serif" }}>
                Panchayat & Department Workspace
              </h3>
              <p style={{ fontSize: "14px", color: "#404B46", lineHeight: 1.6, margin: "0 0 16px" }}>
                Structured operational dashboards for Gram Panchayat staff and department officials. Triage incoming cases, assign to officers, and update resolution notes with full audit logging.
              </p>
              <Link to="/login" style={{
                display: "inline-flex", alignItems: "center", gap: "4px",
                fontSize: "12px", fontWeight: 700, color: "#153D32", textDecoration: "none",
              }}>
                View Staff Demo <ChevronRight size={14} />
              </Link>
            </div>

          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          ACCESSIBILITY & INCLUSION
      ═══════════════════════════════════════════ */}
      <section style={{ padding: "0 0 80px 0", background: "#F8FAFC" }}>
        <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "0 32px" }}>
          <div className="civic-card" style={{ padding: "48px" }}>
            <div style={{ marginBottom: "36px" }}>
              <span style={{
                display: "inline-block", fontSize: "11px", fontWeight: 800, letterSpacing: "1.5px",
                textTransform: "uppercase", color: "#153D32", background: "#EFF5EF",
                border: "1px solid #DDE8DD", padding: "4px 14px", borderRadius: "9999px", marginBottom: "12px",
              }}>
                Civic Accessibility First
              </span>
              <h2 style={{ fontSize: "26px", fontWeight: 800, color: "#17221F", margin: "0 0 10px", fontFamily: "'Plus Jakarta Sans',sans-serif" }}>
                Inclusive Public Service Design
              </h2>
              <p style={{ fontSize: "14px", color: "#404B46", lineHeight: 1.6, maxWidth: "520px" }}>
                Rural governance portals must be usable by everyone, regardless of connectivity, device size, or accessibility requirements.
              </p>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "20px" }}>
              {[
                { Icon: Smartphone, title: "Mobile-First & Lightweight", desc: "Designed for budget Android smartphones and 3G/4G connectivity." },
                { Icon: Eye,        title: "High Contrast (WCAG 2.2 AA)", desc: "Strict color ratios and semantic icons prevent relying on color alone." },
                { Icon: FileText,   title: "Plain Language Interface", desc: "Jargon-free labels ensure non-technical citizens understand their grievance." },
                { Icon: Users,      title: "Full Keyboard Support", desc: "Focus indicators and semantic HTML allow complete portal navigation without a mouse." },
              ].map(({ Icon, title, desc }) => (
                <div key={title} style={{ padding: "16px", background: "#F7F6F0", borderRadius: "12px", border: "1px solid #E5E7DF" }}>
                  <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "#EFF5EF", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "10px" }}>
                    <Icon size={16} style={{ color: "#153D32" }} />
                  </div>
                  <h4 style={{ fontSize: "13px", fontWeight: 700, color: "#17221F", margin: "0 0 6px", fontFamily: "'Plus Jakarta Sans',sans-serif" }}>{title}</h4>
                  <p style={{ fontSize: "12px", color: "#69736D", lineHeight: 1.5, margin: 0 }}>{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          FINAL CTA BANNER
      ═══════════════════════════════════════════ */}
      <section className="civic-panel-forest" style={{ margin: "0 32px 64px", borderRadius: "24px", padding: "72px 48px", textAlign: "center" }}>
        <div style={{ maxWidth: "600px", margin: "0 auto" }}>
          <h2 style={{ fontSize: "clamp(24px,3vw,38px)", fontWeight: 800, color: "#FFFFFF", margin: "0 0 12px", lineHeight: 1.15, fontFamily: "'Plus Jakarta Sans',sans-serif" }}>
            Ready to experience transparent village governance?
          </h2>
          <p style={{ fontSize: "15px", color: "#DDE8DD", marginBottom: "32px", lineHeight: 1.6 }}>
            Lodge a grievance in under 2 minutes or query the verified knowledge base using natural language.
          </p>
          <div style={{ display: "flex", gap: "16px", justifyContent: "center", flexWrap: "wrap" }}>
            <Link to="/submit" className="btn-gis-cyan" style={{ padding: "14px 28px", fontSize: "14px" }}>
              <PlusCircle size={16} />
              <span>Submit a Grievance Now</span>
            </Link>
            <Link to="/ai-assistant" style={{
              display: "inline-flex", alignItems: "center", gap: "8px",
              padding: "14px 28px", borderRadius: "14px", background: "rgba(255,255,255,0.12)",
              color: "#FFFFFF", fontWeight: 700, fontSize: "14px", textDecoration: "none",
              border: "1px solid rgba(255,255,255,0.25)", transition: "background 0.18s",
            }}>
              Ask AI Assistant
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
};

export default LandingPage;