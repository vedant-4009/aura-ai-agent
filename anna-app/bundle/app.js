import { AnnaAppRuntime } from "/static/anna-apps/_sdk/latest/index.js";

const TOOL_ID = window.__ANNA_TOOL_IDS__["aura-ai-agent"];

async function main() {
  const prompt = document.getElementById("prompt");
  const button = document.getElementById("primary-btn");
  const status = document.getElementById("status");
  const results = document.getElementById("results");

  if (!prompt || !button || !status || !results) {
    return;
  }

  let anna;

  try {
    anna = await AnnaAppRuntime.connect();

    await anna.window.set_title({
      title: "AURA LaunchGuard"
    });

    status.textContent = "Ready.";
  } catch (error) {
    status.textContent = "Anna host not connected.";
    return;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function getSeverityClass(severity) {
    return String(severity || "Informational")
      .toLowerCase()
      .replaceAll(" ", "-");
  }

  function getSeverityIcon(severity) {
    const icons = {
      Critical: "🔴",
      High: "🟠",
      Medium: "🟡",
      Low: "🔵",
      Informational: "ℹ️"
    };

    return icons[severity] || "ℹ️";
  }

  function renderStat(label, value, className = "") {
    return `
      <div class="stat ${className}">
        <div class="stat-number">
          ${escapeHtml(value)}
        </div>

        <div class="stat-label">
          ${escapeHtml(label)}
        </div>
      </div>
    `;
  }

  function renderSeveritySummary(severityCounts) {
    const counts = {
      Critical: severityCounts?.Critical ?? 0,
      High: severityCounts?.High ?? 0,
      Medium: severityCounts?.Medium ?? 0,
      Low: severityCounts?.Low ?? 0,
      Informational: severityCounts?.Informational ?? 0
    };

    return `
      <div class="severity-summary">

        <div class="severity-item critical">
          <span class="severity-dot"></span>
          <span>Critical</span>
          <strong>${counts.Critical}</strong>
        </div>

        <div class="severity-item high">
          <span class="severity-dot"></span>
          <span>High</span>
          <strong>${counts.High}</strong>
        </div>

        <div class="severity-item medium">
          <span class="severity-dot"></span>
          <span>Medium</span>
          <strong>${counts.Medium}</strong>
        </div>

        <div class="severity-item low">
          <span class="severity-dot"></span>
          <span>Low</span>
          <strong>${counts.Low}</strong>
        </div>

        <div class="severity-item informational">
          <span class="severity-dot"></span>
          <span>Informational</span>
          <strong>${counts.Informational}</strong>
        </div>

      </div>
    `;
  }

  function renderReadmeSummary(readmeAnalysis) {
    if (!readmeAnalysis) {
      return "";
    }

    const sections = readmeAnalysis.sections || {};

    const sectionNames = [
      ["description", "Description"],
      ["installation", "Installation"],
      ["usage", "Usage"],
      ["configuration", "Configuration"],
      ["deployment", "Deployment"]
    ];

    const items = sectionNames
      .map(([key, label]) => {
        const section = sections[key];

        if (!section) {
          return "";
        }

        const found = section.found;

        return `
          <div class="readme-check ${found ? "pass" : "missing"}">
            <span class="readme-check-icon">
              ${found ? "✓" : "!"}
            </span>

            <span class="readme-check-label">
              ${escapeHtml(label)}
            </span>

            <span class="readme-check-status">
              ${found ? "Detected" : "Missing"}
            </span>
          </div>
        `;
      })
      .join("");

    return `
      <div class="analysis-section">

        <div class="section-heading">
          <div>
            <div class="section-title">
              README Documentation
            </div>

            <div class="section-subtitle">
              Documentation quality analysis
            </div>
          </div>

          <span class="section-badge">
            ${escapeHtml(
              readmeAnalysis.finding_count ?? 0
            )} checks
          </span>
        </div>

        <div class="readme-grid">
          ${items}
        </div>

      </div>
    `;
  }

  function renderSecuritySummary(secretScan) {
    if (!secretScan) {
      return "";
    }

    const secretsExposed = secretScan.secrets_exposed === true;
    const findingCount = secretScan.finding_count ?? 0;

    return `
      <div class="security-panel ${
        secretsExposed ? "security-risk" : "security-safe"
      }">

        <div class="security-icon">
          ${secretsExposed ? "⚠" : "✓"}
        </div>

        <div class="security-content">

          <div class="security-title">
            Secret Scan
          </div>

          <div class="security-text">
            ${
              secretsExposed
                ? "Potential secret exposure requires attention."
                : "No secret-prone filenames detected."
            }
          </div>

          <div class="security-meta">
            Scan:
            ${escapeHtml(
              secretScan.scan_type ||
                "safe_secret_filename_scan"
            )}

            · Findings:
            ${escapeHtml(findingCount)}
          </div>

        </div>

      </div>
    `;
  }

  function renderFinding(finding) {
    const severity =
      finding?.severity || "Informational";

    const severityClass =
      getSeverityClass(severity);

    const icon =
      getSeverityIcon(severity);

    const title =
      escapeHtml(
        finding?.title ||
          "Untitled finding"
      );

    const fact =
      escapeHtml(
        finding?.fact ||
          "No fact recorded."
      );

    const recommendation =
      escapeHtml(
        finding?.recommendation ||
          "No recommendation recorded."
      );

    const evidence = Array.isArray(
      finding?.evidence
    )
      ? finding.evidence
      : [];

    const evidenceHtml = evidence.length
      ? evidence
          .map(
            item => `
              <div class="evidence-item">
                ${escapeHtml(item)}
              </div>
            `
          )
          .join("")
      : `
          <div class="evidence-item">
            No evidence recorded.
          </div>
        `;

    return `
      <article class="finding ${severityClass}">

        <div class="finding-top">

          <div class="finding-heading">

            <span class="finding-icon">
              ${icon}
            </span>

            <span class="finding-title">
              ${title}
            </span>

          </div>

          <span class="severity ${severityClass}">
            ${escapeHtml(severity)}
          </span>

        </div>

        <div class="finding-section">

          <div class="finding-label">
            Fact
          </div>

          <div class="finding-text">
            ${fact}
          </div>

        </div>

        <div class="finding-section">

          <div class="finding-label">
            Evidence
          </div>

          <div class="evidence">
            ${evidenceHtml}
          </div>

        </div>

        <div class="finding-section">

          <div class="finding-label">
            Recommendation
          </div>

          <div class="recommendation">
            ${recommendation}
          </div>

        </div>

      </article>
    `;
  }

  function renderAnalysis(data) {
    const execution =
      data?.execution?.results?.["1"]?.result;

    if (!execution?.success) {
      results.innerHTML = `
        <div class="error">
          <strong>Analysis could not be completed.</strong>
          <div>
            The AURA execution did not return a valid
            release-readiness result.
          </div>
        </div>
      `;

      return;
    }

    const findings =
      Array.isArray(execution.findings)
        ? execution.findings
        : [];

    const repository =
      execution.repository ||
      "Unknown repository";

    const severityCounts =
      execution.severity_counts || {};

    const readmeAnalysis =
      execution.readme_analysis || null;

    const secretScan =
      execution.secret_scan || null;

    const critical =
      severityCounts.Critical ??
      findings.filter(
        item => item.severity === "Critical"
      ).length;

    const high =
      severityCounts.High ??
      findings.filter(
        item => item.severity === "High"
      ).length;

    const medium =
      severityCounts.Medium ??
      findings.filter(
        item => item.severity === "Medium"
      ).length;

    const low =
      severityCounts.Low ??
      findings.filter(
        item => item.severity === "Low"
      ).length;

    const informational =
      severityCounts.Informational ??
      findings.filter(
        item => item.severity === "Informational"
      ).length;

    results.innerHTML = `

      <div class="analysis-header">

        <div>

          <div class="panel-title">
            Release Readiness
          </div>

          <div class="repository">
            Repository:
            <strong>
              ${escapeHtml(repository)}
            </strong>
          </div>

        </div>

        <div class="analysis-status">
          ✓ Analysis complete
        </div>

      </div>

      <div class="summary">

        ${renderStat(
          "Total Findings",
          findings.length
        )}

        ${renderStat(
          "Critical / High",
          critical + high,
          critical + high > 0
            ? "danger"
            : "safe"
        )}

        ${renderStat(
          "Medium",
          medium,
          medium > 0
            ? "warning"
            : "safe"
        )}

        ${renderStat(
          "Low",
          low
        )}

        ${renderStat(
          "Informational",
          informational
        )}

      </div>

      ${renderSeveritySummary(
        severityCounts
      )}

      ${renderSecuritySummary(
        secretScan
      )}

      ${renderReadmeSummary(
        readmeAnalysis
      )}

      <div class="analysis-section">

        <div class="section-heading">

          <div>

            <div class="section-title">
              Findings
            </div>

            <div class="section-subtitle">
              Evidence-based release readiness observations
            </div>

          </div>

          <span class="section-badge">
            ${findings.length} total
          </span>

        </div>

        <div class="findings">

          ${
            findings.length
              ? findings
                  .map(renderFinding)
                  .join("")
              : `
                <div class="empty">
                  No release-readiness findings detected.
                </div>
              `
          }

        </div>

      </div>

    `;
  }

  button.addEventListener(
    "click",
    async () => {
      const input =
        prompt.value.trim();

      if (!input) {
        status.textContent =
          "Please enter a repository request.";

        return;
      }

      button.disabled = true;

      status.textContent =
        "Analyzing repository...";

      results.innerHTML = `
        <div class="loading-state">

          <div class="loading-spinner"></div>

          <div>
            <strong>
              AURA is analyzing the repository
            </strong>

            <div>
              Collecting repository evidence and
              checking release readiness...
            </div>
          </div>

        </div>
      `;

      try {
        const result =
          await anna.tools.invoke({
            tool_id: TOOL_ID,
            method: "run",
            args: {
              input
            }
          });

        if (result?.success === false) {
          throw new Error(
            result.error ||
              "AURA execution failed."
          );
        }

        const data =
          result?.data ?? result;

        renderAnalysis(data);

        status.textContent =
          "Analysis completed.";

        await anna.storage.set({
          key: "aura-ai-agent:last",
          value: Date.now()
        });

      } catch (error) {
        status.textContent =
          "Analysis failed.";

        results.innerHTML = `
          <div class="error">

            <strong>
              Analysis failed
            </strong>

            <div>
              ${escapeHtml(
                error?.message ||
                  "Unknown error."
              )}
            </div>

          </div>
        `;
      } finally {
        button.disabled = false;
      }
    }
  );
}

main();

