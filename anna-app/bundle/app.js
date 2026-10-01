import { AnnaAppRuntime } from "/static/anna-apps/_sdk/latest/index.js";

const TOOL_ID = "tool-dev-aura-ai-agent";

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

  function renderAnalysis(data) {
    const execution =
      data?.execution?.results?.["1"]?.result;

    if (!execution?.success) {
      results.innerHTML = `
        <div class="error">
          Analysis could not be completed.
        </div>
      `;
      return;
    }

    const findings = execution.findings || [];
    const repository = execution.repository || "Unknown repository";

    const critical = findings.filter(
      item => item.severity === "Critical"
    ).length;

    const high = findings.filter(
      item => item.severity === "High"
    ).length;

    const medium = findings.filter(
      item => item.severity === "Medium"
    ).length;

    results.innerHTML = `
      <div class="panel-title">Release Readiness</div>

      <div class="repository">
        Repository:
        <strong>${escapeHtml(repository)}</strong>
      </div>

      <div class="summary">
        <div class="stat">
          <div class="stat-number">${findings.length}</div>
          <div class="stat-label">Total Findings</div>
        </div>

        <div class="stat">
          <div class="stat-number">${critical + high}</div>
          <div class="stat-label">Critical / High</div>
        </div>

        <div class="stat">
          <div class="stat-number">${medium}</div>
          <div class="stat-label">Medium</div>
        </div>
      </div>

      <div class="findings">
        ${
          findings.length
            ? findings.map(renderFinding).join("")
            : `
              <div class="empty">
                No release-readiness findings detected.
              </div>
            `
        }
      </div>
    `;
  }

  function renderFinding(finding) {
    const severity = escapeHtml(finding.severity);
    const title = escapeHtml(finding.title);
    const fact = escapeHtml(finding.fact);
    const recommendation = escapeHtml(
      finding.recommendation
    );

    const evidence = (finding.evidence || [])
      .map(
        item =>
          `<span>${escapeHtml(item)}</span>`
      )
      .join("");

    return `
      <article class="finding">

        <div class="finding-top">
          <span class="severity">
            ${severity}
          </span>

          <span class="finding-title">
            ${title}
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
            ${evidence || "<span>No evidence recorded</span>"}
          </div>
        </div>

        <div class="finding-section">
          <div class="finding-label">
            Recommendation
          </div>

          <div class="finding-text">
            ${recommendation}
          </div>
        </div>

      </article>
    `;
  }

  button.addEventListener("click", async () => {
    const input = prompt.value.trim();

    if (!input) {
      status.textContent = "Please enter a repository request.";
      return;
    }

    button.disabled = true;
    status.textContent = "Analyzing repository...";

    results.innerHTML = `
      <div class="empty">
        AURA is analyzing the repository and collecting evidence...
      </div>
    `;

    try {
      const result = await anna.tools.invoke({
        tool_id: TOOL_ID,
        method: "run",
        args: {
          input
        }
      });

      if (result?.success === false) {
        throw new Error(
          result.error || "AURA execution failed."
        );
      }

      const data = result?.data ?? result;

      renderAnalysis(data);

      status.textContent = "Analysis completed.";

      await anna.storage.set({
        key: "aura-ai-agent:last",
        value: Date.now()
      });

    } catch (error) {
      status.textContent = "Analysis failed.";

      results.innerHTML = `
        <div class="error">
          <strong>Error:</strong>
          ${escapeHtml(error.message)}
        </div>
      `;
    } finally {
      button.disabled = false;
    }
  });
}

main();