// ClaimLens Dashboard Dynamic JavaScript

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const sampleSelect = document.getElementById('sample-select');
  const btnLoadSample = document.getElementById('btn-load-sample');
  const btnRunReview = document.getElementById('btn-run-review');
  const payloadJson = document.getElementById('payload-json');
  const apiStatusBadge = document.getElementById('api-status-badge');
  
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

  // Tab Switching
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      document.getElementById(targetId).classList.add('active');
    });
  });

  // Check API Health
  fetch('/api/health')
    .then(res => res.json())
    .then(data => {
      if (data.gemini_api_key_configured) {
        apiStatusBadge.textContent = 'Gemini API Configured';
        apiStatusBadge.className = 'badge status-badge online';
      } else {
        apiStatusBadge.textContent = 'Offline Engine (No Key Set)';
        apiStatusBadge.className = 'badge status-badge fallback';
      }
    })
    .catch(() => {
      apiStatusBadge.textContent = 'Backend Error';
      apiStatusBadge.className = 'badge status-badge fallback';
    });

  // Load List of Sample Claims
  fetch('/api/claims')
    .then(res => res.json())
    .then(claims => {
      sampleSelect.innerHTML = '<option value="">-- Choose Sample Case --</option>';
      claims.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.filename;
        opt.textContent = `${c.claim_id}: ${c.case_name}`;
        sampleSelect.appendChild(opt);
      });
      // Auto select first sample
      if (claims.length > 0) {
        sampleSelect.selectedIndex = 1;
        loadSampleClaim(claims[0].filename);
      }
    })
    .catch(err => console.error("Failed to fetch claims list:", err));

  // Event: Load Sample Claim Button
  btnLoadSample.addEventListener('click', () => {
    const selected = sampleSelect.value;
    if (selected) {
      loadSampleClaim(selected);
    }
  });

  sampleSelect.addEventListener('change', () => {
    if (sampleSelect.value) {
      loadSampleClaim(sampleSelect.value);
    }
  });

  function loadSampleClaim(filename) {
    fetch(`/api/claims/${filename}`)
      .then(res => res.json())
      .then(data => {
        payloadJson.value = JSON.stringify(data, null, 2);
      })
      .catch(err => alert("Error loading claim: " + err));
  }

  // Event: Run Evidence Review Button
  btnRunReview.addEventListener('click', () => {
    const rawJson = payloadJson.value.trim();
    if (!rawJson) {
      alert("Please paste or select a claim JSON payload first.");
      return;
    }

    let payloadObj;
    try {
      payloadObj = JSON.parse(rawJson);
    } catch (e) {
      alert("Invalid JSON format in claim payload editor: " + e.message);
      return;
    }

    // Show Loading
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
        alert("Review failed: " + err.message);
      });
  });

  function renderReviewResults(res) {
    reviewContent.classList.remove('hidden');

    // Recommendation Banner
    recText.textContent = res.overall_recommendation;
    recText.className = `recommendation-badge ${res.overall_recommendation}`;

    completenessPill.textContent = res.completeness_status;
    consistencyPill.textContent = res.consistency_status;
    confidencePill.textContent = `${res.confidence_level} CONFIDENCE`;

    aiModePill.textContent = res.ai_mode === 'GEMINI_POWERED' ? '✨ Gemini GenAI Powered' : '⚙️ Deterministic Engine';

    // Escalation Banner
    if (res.human_escalation_required) {
      escBanner.classList.remove('hidden');
      escReasonText.textContent = res.escalation_reason || "Evidence requires human review.";
    } else {
      escBanner.classList.add('hidden');
    }

    // Executive Summary
    summaryText.textContent = res.ai_reasoning_summary;

    // Contradictions
    const contraList = document.getElementById('contradictions-list');
    badgeContraCount.textContent = res.contradictions ? res.contradictions.length : 0;
    contraList.innerHTML = '';

    if (!res.contradictions || res.contradictions.length === 0) {
      contraList.innerHTML = `
        <div class="item-card success">
          <div class="item-title">✓ No Document Contradictions Detected</div>
          <div class="item-detail">All submitted claim documents show consistent field values.</div>
        </div>
      `;
    } else {
      res.contradictions.forEach(c => {
        contraList.innerHTML += `
          <div class="item-card danger">
            <div class="item-header">
              <div class="item-title">⚠️ Field Discrepancy: ${c.field_name}</div>
              <span class="item-badge" style="background: rgba(239,68,68,0.2); color:#ef4444;">CONTRADICTION</span>
            </div>
            <div class="item-grid">
              <div><strong>Value A:</strong> ${c.value_a}<br><small style="color:#9ca3af;">(${c.source_a})</small></div>
              <div><strong>Value B:</strong> ${c.value_b}<br><small style="color:#9ca3af;">(${c.source_b})</small></div>
            </div>
            <div class="item-detail"><strong>Impact:</strong> ${c.impact_explanation}</div>
            <div class="item-detail"><strong>Recommendation:</strong> ${c.recommended_action}</div>
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
        <div class="item-card ${isPass ? 'success' : 'danger'}">
          <div class="item-header">
            <div class="item-title">${isPass ? '✓' : '✗'} ${chk.check_name}</div>
            <span class="item-badge" style="background:${isPass ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}; color:${isPass ? '#10b981' : '#ef4444'};">
              ${chk.policy_clause_id}
            </span>
          </div>
          <div class="item-detail">${chk.details}</div>
          <div class="item-detail" style="font-size:11.5px; color:#6b7280;">Sources: ${chk.source_fields.join(', ')}</div>
        </div>
      `;
    });

    // Policy Citations (RAG)
    const clausesList = document.getElementById('policy-clauses-list');
    clausesList.innerHTML = '';
    res.applicable_policy_clauses.forEach(cl => {
      clausesList.innerHTML += `
        <div class="item-card">
          <div class="item-header">
            <div class="item-title">[${cl.clause_id}] ${cl.title}</div>
            <span class="item-badge" style="background:rgba(59,130,246,0.2); color:#60a5fa;">${cl.category}</span>
          </div>
          <div class="item-detail" style="font-style:italic;">"${cl.text}"</div>
          <div class="item-detail"><strong>Relevance:</strong> ${cl.applicability_reason}</div>
        </div>
      `;
    });

    // Evidence Findings
    const findingsList = document.getElementById('findings-list');
    findingsList.innerHTML = '';
    res.evidence_findings.forEach(f => {
      findingsList.innerHTML += `
        <div class="item-card">
          <div class="item-header">
            <div class="item-title">${f.summary}</div>
            <span class="item-badge" style="background:rgba(255,255,255,0.1); color:#d1d5db;">${f.finding_type}</span>
          </div>
          <div class="item-detail"><strong>Evidence Source:</strong> ${f.evidence_source}</div>
          <div class="item-detail"><strong>Policy Basis:</strong> ${f.policy_clause}</div>
          <div class="item-detail"><strong>Reasoning:</strong> ${f.reasoning}</div>
        </div>
      `;
    });

    // Investigator Next Steps
    const stepsList = document.getElementById('next-steps-list');
    stepsList.innerHTML = '';
    res.investigator_next_steps.forEach(step => {
      stepsList.innerHTML += `<li>${step}</li>`;
    });

    // Unknowns & Ambiguities
    const unknownsList = document.getElementById('unknowns-list');
    unknownsList.innerHTML = '';
    if (!res.unknowns_and_ambiguities || res.unknowns_and_ambiguities.length === 0) {
      unknownsList.innerHTML = `<li>No critical ambiguities identified.</li>`;
    } else {
      res.unknowns_and_ambiguities.forEach(unk => {
        unknownsList.innerHTML += `<li>${unk}</li>`;
      });
    }
  }
});
