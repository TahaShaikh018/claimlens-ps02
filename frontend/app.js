// ClaimLens Workstation Dynamic JavaScript (Shadcn/UI Architecture)

document.addEventListener('DOMContentLoaded', () => {
  // DOM Element References
  const sampleSelect = document.getElementById('sample-select');
  const claimsQueueList = document.getElementById('claims-queue-list');
  const queueCountBadge = document.getElementById('queue-count-badge');
  const btnLoadSample = document.getElementById('btn-load-sample');
  const btnRunReview = document.getElementById('btn-run-review');
  const payloadJson = document.getElementById('payload-json');
  const apiStatusBadge = document.getElementById('api-status-badge');
  
  const btnTogglePayload = document.getElementById('btn-toggle-payload');
  const payloadContainer = document.getElementById('payload-container');
  const payloadToggleIcon = document.getElementById('payload-toggle-icon');

  const activeClaimId = document.getElementById('active-claim-id');
  const activeClaimMeta = document.getElementById('active-claim-meta');

  const emptyState = document.getElementById('empty-state');
  const loadingState = document.getElementById('loading-state');
  const reviewContent = document.getElementById('review-content');
  const aiModePill = document.getElementById('ai-mode-pill');
  
  const recBanner = document.getElementById('recommendation-banner');
  const recText = document.getElementById('recommendation-text');
  const completenessPill = document.getElementById('completeness-pill');
  const consistencyPill = document.getElementById('consistency-pill');
  const confidencePill = document.getElementById('confidence-pill');
  
  const escBanner = document.getElementById('escalation-banner');
  const escReasonText = document.getElementById('escalation-reason-text');
  const summaryText = document.getElementById('reasoning-summary-text');
  const badgeContraCount = document.getElementById('badge-contradiction-count');

  // Input & Modal References
  const btnOpenCreateModal = document.getElementById('btn-open-create-modal');
  const btnCloseModal = document.getElementById('btn-close-modal');
  const btnCancelModal = document.getElementById('btn-cancel-modal');
  const customClaimModal = document.getElementById('custom-claim-modal');
  const btnSubmitModal = document.getElementById('btn-submit-modal');
  const createClaimForm = document.getElementById('create-claim-form');

  const btnTriggerUpload = document.getElementById('btn-trigger-upload');
  const fileInputClaim = document.getElementById('file-input-claim');

  let loadedClaimsData = [];
  let customClaimsQueue = [];

  // Toggle Payload Drawer
  if (btnTogglePayload) {
    btnTogglePayload.addEventListener('click', () => {
      payloadContainer.classList.toggle('hidden');
      payloadToggleIcon.textContent = payloadContainer.classList.contains('hidden') ? '▼' : '▲';
    });
  }

  // Modal Handlers
  if (btnOpenCreateModal) {
    btnOpenCreateModal.addEventListener('click', () => {
      customClaimModal.classList.remove('hidden');
    });
  }

  function closeModal() {
    customClaimModal.classList.add('hidden');
  }

  if (btnCloseModal) btnCloseModal.addEventListener('click', closeModal);
  if (btnCancelModal) btnCancelModal.addEventListener('click', closeModal);

  // File Upload Handler
  if (btnTriggerUpload && fileInputClaim) {
    btnTriggerUpload.addEventListener('click', () => fileInputClaim.click());

    fileInputClaim.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const parsed = JSON.parse(event.target.result);
          
          // Basic payload structure check
          if (!parsed.claim_id) {
            alert("Uploaded JSON missing required field 'claim_id'.");
            return;
          }

          const filenameKey = `uploaded_${Date.now()}`;
          const customClaimObj = {
            filename: filenameKey,
            claim_id: parsed.claim_id,
            case_name: parsed.case_name || "Uploaded Custom Claim",
            data: parsed
          };

          customClaimsQueue.unshift(customClaimObj);
          updateFullQueueView();
          setActiveCustomClaim(customClaimObj);
          fileInputClaim.value = '';

        } catch (err) {
          alert("Failed to parse uploaded JSON file: " + err.message);
        }
      };
      reader.readAsText(file);
    });
  }

  // Custom Claim Form Submission
  if (btnSubmitModal) {
    btnSubmitModal.addEventListener('click', (e) => {
      e.preventDefault();

      const claimId = document.getElementById('form-claim-id').value.trim() || `CLM-CUSTOM-${Date.now()}`;
      const caseName = document.getElementById('form-case-name').value.trim() || 'Custom Claim';
      const claimType = document.getElementById('form-claim-type').value;
      const vehicleType = document.getElementById('form-vehicle-type').value;
      const vehicleModel = document.getElementById('form-vehicle-model').value.trim();
      const regNumber = document.getElementById('form-reg-number').value.trim();
      const idv = parseFloat(document.getElementById('form-idv').value) || 500000;
      const claimedAmount = parseFloat(document.getElementById('form-claimed-amount').value) || 50000;
      const incidentDate = document.getElementById('form-incident-date').value;
      const reportDate = document.getElementById('form-report-date').value;
      const location = document.getElementById('form-location').value.trim();
      const description = document.getElementById('form-description').value.trim();

      const docs = [];

      if (document.getElementById('chk-doc-claimform').checked) {
        docs.push({
          doc_type: "Claim Form",
          doc_id: "CF-001",
          fields: {
            claimant_name: "Insured Policyholder",
            vehicle_registration: regNumber,
            incident_date: incidentDate,
            report_date: reportDate,
            incident_location: location,
            incident_cause: description.substring(0, 50),
            claimed_amount: claimedAmount
          }
        });
      }

      if (document.getElementById('chk-doc-estimate').checked) {
        docs.push({
          doc_type: "Repair Estimate",
          doc_id: "EST-001",
          fields: {
            repairer_name: "Authorized Workshop",
            estimate_date: reportDate,
            repair_estimate_amount: claimedAmount,
            repaired_parts_summary: "Front bumper replacement & body alignment"
          }
        });
      }

      if (document.getElementById('chk-doc-fir').checked) {
        docs.push({
          doc_type: "FIR Report",
          doc_id: "FIR-001",
          fields: {
            fir_number: `FIR-${Math.floor(Math.random()*1000)}`,
            fir_date: reportDate,
            police_station: "Central City Station",
            incident_type: claimType
          }
        });
      }

      const generatedPayload = {
        claim_id: claimId,
        case_name: caseName,
        claim_type: claimType,
        vehicle_type: vehicleType,
        vehicle_model: vehicleModel,
        registration_number: regNumber,
        insured_declared_value: idv,
        incident_date: incidentDate,
        report_date: reportDate,
        incident_location: location,
        claimed_amount: claimedAmount,
        customer_description: description,
        submitted_documents: docs
      };

      const filenameKey = `custom_${Date.now()}`;
      const customClaimObj = {
        filename: filenameKey,
        claim_id: claimId,
        case_name: caseName,
        data: generatedPayload
      };

      customClaimsQueue.unshift(customClaimObj);
      updateFullQueueView();
      setActiveCustomClaim(customClaimObj);
      closeModal();
      
      // Auto execute review
      btnRunReview.click();
    });
  }

  function setActiveCustomClaim(obj) {
    payloadJson.value = JSON.stringify(obj.data, null, 2);
    if (activeClaimId) activeClaimId.textContent = obj.claim_id;
    if (activeClaimMeta) activeClaimMeta.textContent = `${obj.data.vehicle_model} (${obj.data.registration_number}) • Incident: ${obj.data.incident_date}`;
    
    // Highlight item
    const allCards = document.querySelectorAll('.queue-card');
    allCards.forEach(card => {
      if (card.dataset.filename === obj.filename) {
        card.classList.add('active');
      } else {
        card.classList.remove('active');
      }
    });
  }

  // Tab Switching (Shadcn Tabs)
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        targetEl.classList.add('active');
      }
    });
  });

  // Check API Health Status
  fetch('/api/health')
    .then(res => res.json())
    .then(data => {
      if (data.gemini_api_key_configured) {
        apiStatusBadge.textContent = 'Gemini API Connected';
        apiStatusBadge.className = 'badge status-badge online';
      } else {
        apiStatusBadge.textContent = 'Offline Engine (Fallback)';
        apiStatusBadge.className = 'badge status-badge fallback';
      }
    })
    .catch(() => {
      apiStatusBadge.textContent = 'Backend Error';
      apiStatusBadge.className = 'badge status-badge fallback';
    });

  // Load Pre-Loaded Demo Claims Queue
  fetch('/api/claims')
    .then(res => res.json())
    .then(claims => {
      loadedClaimsData = claims;
      
      // Populate hidden select for backward compatibility
      sampleSelect.innerHTML = '<option value="">-- Choose Sample Case --</option>';
      claims.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.filename;
        opt.textContent = `${c.claim_id}: ${c.case_name}`;
        sampleSelect.appendChild(opt);
      });

      updateFullQueueView();

      // Auto Select First Claim (CLM-2026-001)
      if (claims.length > 0) {
        selectClaimByFilename(claims[0].filename);
      }
    })
    .catch(err => console.error("Failed to fetch claims list:", err));

  function updateFullQueueView() {
    if (!claimsQueueList) return;
    claimsQueueList.innerHTML = '';

    const totalCount = loadedClaimsData.length + customClaimsQueue.length;
    if (queueCountBadge) queueCountBadge.textContent = `${totalCount} Cases`;

    // 1. Custom Claims First
    customClaimsQueue.forEach(c => {
      const card = document.createElement('div');
      card.className = 'queue-card';
      card.dataset.filename = c.filename;

      card.innerHTML = `
        <div class="queue-card-top">
          <span class="claim-id-text">${c.claim_id}</span>
          <span class="badge status-badge online">CUSTOM INPUT</span>
        </div>
        <div class="queue-card-title">${c.case_name}</div>
        <div class="queue-card-meta">
          <span>Source: Interactive Input</span>
        </div>
      `;

      card.addEventListener('click', () => {
        setActiveCustomClaim(c);
      });

      claimsQueueList.appendChild(card);
    });

    // 2. Pre-Loaded Demo Claims
    loadedClaimsData.forEach(c => {
      const card = document.createElement('div');
      card.className = 'queue-card';
      card.dataset.filename = c.filename;

      let statusBadgeClass = 'badge-secondary';
      let statusLabel = 'PENDING';
      if (c.case_name.includes('Approvable')) {
        statusBadgeClass = 'status-badge online';
        statusLabel = 'APPROVABLE';
      } else if (c.case_name.includes('Contradiction')) {
        statusBadgeClass = 'badge-danger';
        statusLabel = 'CONTRADICTION';
      } else if (c.case_name.includes('Missing')) {
        statusBadgeClass = 'status-badge fallback';
        statusLabel = 'MISSING DOC';
      } else if (c.case_name.includes('Exclusion')) {
        statusBadgeClass = 'badge-danger';
        statusLabel = 'EXCLUSION';
      } else if (c.case_name.includes('Uncertain')) {
        statusBadgeClass = 'status-badge fallback';
        statusLabel = 'UNCERTAIN';
      }

      card.innerHTML = `
        <div class="queue-card-top">
          <span class="claim-id-text">${c.claim_id}</span>
          <span class="badge ${statusBadgeClass}">${statusLabel}</span>
        </div>
        <div class="queue-card-title">${c.case_name}</div>
        <div class="queue-card-meta">
          <span>File: ${c.filename}</span>
        </div>
      `;

      card.addEventListener('click', () => {
        selectClaimByFilename(c.filename);
      });

      claimsQueueList.appendChild(card);
    });
  }

  function selectClaimByFilename(filename) {
    // Check if it's custom first
    const customMatch = customClaimsQueue.find(c => c.filename === filename);
    if (customMatch) {
      setActiveCustomClaim(customMatch);
      return;
    }

    // Highlight sidebar item
    const allCards = document.querySelectorAll('.queue-card');
    allCards.forEach(card => {
      if (card.dataset.filename === filename) {
        card.classList.add('active');
      } else {
        card.classList.remove('active');
      }
    });

    sampleSelect.value = filename;
    loadSampleClaim(filename);
  }

  function loadSampleClaim(filename) {
    fetch(`/api/claims/${filename}`)
      .then(res => res.json())
      .then(data => {
        payloadJson.value = JSON.stringify(data, null, 2);
        
        const claimId = data.claim_id || filename;
        const vehicle = `${data.vehicle_model || ''} (${data.registration_number || ''})`;
        const incidentDate = data.incident_date || '';
        
        if (activeClaimId) activeClaimId.textContent = claimId;
        if (activeClaimMeta) activeClaimMeta.textContent = `${vehicle} • Incident: ${incidentDate}`;
      })
      .catch(err => alert("Error loading claim payload: " + err));
  }

  if (btnLoadSample) {
    btnLoadSample.addEventListener('click', () => {
      if (sampleSelect.value) {
        loadSampleClaim(sampleSelect.value);
      }
    });
  }

  sampleSelect.addEventListener('change', () => {
    if (sampleSelect.value) {
      selectClaimByFilename(sampleSelect.value);
    }
  });

  // Event Listener: Run Review Button
  btnRunReview.addEventListener('click', () => {
    const rawJson = payloadJson.value.trim();
    if (!rawJson) {
      alert("Please select a claim from the queue or enter JSON payload first.");
      return;
    }

    let payloadObj;
    try {
      payloadObj = JSON.parse(rawJson);
    } catch (e) {
      alert("Invalid JSON format in claim payload: " + e.message);
      return;
    }

    // Show Loading State
    emptyState.classList.add('hidden');
    reviewContent.classList.add('hidden');
    loadingState.classList.remove('hidden');

    fetch('/api/review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payloadObj)
    })
      .then(res => {
        if (!res.ok) {
          return res.json().then(err => { throw new Error(err.detail || "Server error"); });
        }
        return res.json();
      })
      .then(review => {
        loadingState.classList.add('hidden');
        renderReviewResults(review);
      })
      .catch(err => {
        loadingState.classList.add('hidden');
        emptyState.classList.remove('hidden');
        alert("Review execution failed: " + err.message);
      });
  });

  function renderReviewResults(res) {
    reviewContent.classList.remove('hidden');

    // Recommendation Banner Metrics
    recText.textContent = res.overall_recommendation;
    recText.className = `recommendation-badge ${res.overall_recommendation.replace(/\s+/g, '_')}`;

    completenessPill.textContent = res.completeness_status;
    consistencyPill.textContent = res.consistency_status;
    confidencePill.textContent = `${res.confidence_level} CONFIDENCE`;

    aiModePill.textContent = res.ai_mode === 'GEMINI_POWERED' ? '✨ Gemini GenAI Powered' : '⚙️ Deterministic Engine';

    // Escalation Banner Alert
    if (res.human_escalation_required) {
      escBanner.classList.remove('hidden');
      escReasonText.textContent = res.escalation_reason || "Evidence requires human investigator verification.";
    } else {
      escBanner.classList.add('hidden');
    }

    // AI Reasoning Executive Summary
    summaryText.textContent = res.ai_reasoning_summary;

    // Contradictions Rendering
    const contraList = document.getElementById('contradictions-list');
    badgeContraCount.textContent = res.contradictions ? res.contradictions.length : 0;
    contraList.innerHTML = '';

    if (!res.contradictions || res.contradictions.length === 0) {
      contraList.innerHTML = `
        <div class="no-contradictions-box">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span>No Document Contradictions Detected — All submitted claim facts match consistently across sources.</span>
        </div>
      `;
    } else {
      res.contradictions.forEach(c => {
        contraList.innerHTML += `
          <div class="contradiction-card">
            <div class="contradiction-card-header">
              <span class="field-badge">DISCREPANCY FIELD: ${c.field_name}</span>
              <span class="badge badge-danger">CONTRADICTION DETECTED</span>
            </div>

            <div class="comparison-grid">
              <div class="comparison-col">
                <span class="source-tag">Source A (${c.source_a})</span>
                <div class="value-box">${c.value_a}</div>
              </div>
              <div class="vs-badge">VS</div>
              <div class="comparison-col">
                <span class="source-tag">Source B (${c.source_b})</span>
                <div class="value-box">${c.value_b}</div>
              </div>
            </div>

            <div class="impact-box">
              <strong>Impact Explanation:</strong> ${c.impact_explanation}
            </div>

            <div class="recommended-action-box">
              <strong>Recommended Action:</strong> ${c.recommended_action}
            </div>
          </div>
        `;
      });
    }

    // Deterministic Checks
    const detList = document.getElementById('deterministic-checks-list');
    detList.innerHTML = '';
    res.deterministic_checks.forEach(chk => {
      const isPass = chk.passed;
      detList.innerHTML += `
        <div class="data-card" style="border-left: 4px solid ${isPass ? 'var(--status-approve)' : 'var(--status-reject)'};">
          <div class="data-card-header">
            <span class="data-title">${isPass ? '✓' : '✗'} ${chk.check_name}</span>
            <span class="clause-tag">${chk.policy_clause_id}</span>
          </div>
          <div style="font-size:13px; color:var(--text-secondary);">${chk.details}</div>
          <div style="font-size:11.5px; color:var(--text-muted);">Evidence Sources: ${chk.source_fields.join(', ')}</div>
        </div>
      `;
    });

    // Policy Citations (RAG)
    const clausesList = document.getElementById('policy-clauses-list');
    clausesList.innerHTML = '';
    res.applicable_policy_clauses.forEach(cl => {
      clausesList.innerHTML += `
        <div class="data-card">
          <div class="data-card-header">
            <span class="data-title">[${cl.clause_id}] ${cl.title}</span>
            <span class="badge badge-secondary">${cl.category}</span>
          </div>
          <div class="clause-quote">"${cl.text}"</div>
          <div style="font-size:12.5px; color:var(--text-secondary);"><strong>Applicability Grounding:</strong> ${cl.applicability_reason}</div>
        </div>
      `;
    });

    // Evidence Findings
    const findingsList = document.getElementById('findings-list');
    findingsList.innerHTML = '';
    res.evidence_findings.forEach(f => {
      findingsList.innerHTML += `
        <div class="data-card">
          <div class="data-card-header">
            <span class="data-title">${f.summary}</span>
            <span class="badge badge-secondary">${f.finding_type}</span>
          </div>
          <div style="font-size:12.5px; color:var(--text-secondary);"><strong>Evidence Source:</strong> ${f.evidence_source}</div>
          <div style="font-size:12.5px; color:var(--text-secondary);"><strong>Policy Basis:</strong> ${f.policy_clause}</div>
          <div style="font-size:12.5px; color:var(--text-muted);">${f.reasoning}</div>
        </div>
      `;
    });

    // Investigator Action Plan
    const stepsList = document.getElementById('next-steps-list');
    stepsList.innerHTML = '';
    res.investigator_next_steps.forEach(step => {
      stepsList.innerHTML += `<li>${step}</li>`;
    });

    // Unknowns & Ambiguities
    const unknownsList = document.getElementById('unknowns-list');
    unknownsList.innerHTML = '';
    if (!res.unknowns_and_ambiguities || res.unknowns_and_ambiguities.length === 0) {
      unknownsList.innerHTML = `<li class="empty-list-text">No critical ambiguities identified.</li>`;
    } else {
      res.unknowns_and_ambiguities.forEach(unk => {
        unknownsList.innerHTML += `<li>${unk}</li>`;
      });
    }
  }
});
