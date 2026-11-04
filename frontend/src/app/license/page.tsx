import type { Metadata } from "next";

import { DocumentFrame } from "@/components/site-chrome";
import { LicenseCopyButton } from "@/components/license-copy-btn";

export const metadata: Metadata = {
  title: "MIT License: Open Source Terms",
  description: "Aerospace open source dossier and MIT licensing terms for FieldWeaver.",
};

const licenseText = `MIT License

Copyright (c) 2026 FieldWeaver contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.`;

export default function LicensePage() {
  return (
    <DocumentFrame active="license">
      <main className="document-main policy-main license-main">
        <section className="document-hero policy-hero">
          <p className="eyebrow">
            <span className="eyebrow-mark" aria-hidden="true" />
            PROJECT TERMS: OPEN SOURCE LICENSE
          </p>
          <h1>
            Built to be<br />
            <em>used and studied.</em>
          </h1>
          <p className="document-lede">
            FieldWeaver&apos;s source code is released under the permissive MIT License for academic,
            research, and commercial development.
          </p>
          <div className="doc-hero-meta">
            <span>SPDX: MIT</span>
            <span>COPYRIGHT 2026 FIELDWEAVER CONTRIBUTORS</span>
            <span>STATUS: PERMISSIVE</span>
          </div>
        </section>

        {/* 3-Column Permission Matrix */}
        <section className="license-matrix-section" aria-label="License terms summary">
          <div className="license-matrix-grid">
            <div className="license-matrix-card perm-card">
              <div className="matrix-card-header">
                <span className="matrix-icon">✓</span>
                <h3>PERMISSIONS</h3>
              </div>
              <ul className="matrix-list">
                <li><strong>Commercial Use:</strong> You may use and integrate the software for commercial projects.</li>
                <li><strong>Modification:</strong> You may modify, adapt, and build upon the source code.</li>
                <li><strong>Distribution:</strong> You may distribute original or modified copies.</li>
                <li><strong>Private Use:</strong> You may run modified versions privately without publishing source.</li>
              </ul>
            </div>

            <div className="license-matrix-card cond-card">
              <div className="matrix-card-header">
                <span className="matrix-icon">!</span>
                <h3>CONDITIONS</h3>
              </div>
              <ul className="matrix-list">
                <li><strong>License and Copyright Notice:</strong> A copy of the copyright notice and this permission notice must be included in all copies or substantial portions of the Software.</li>
              </ul>
            </div>

            <div className="license-matrix-card limit-card">
              <div className="matrix-card-header">
                <span className="matrix-icon">✕</span>
                <h3>LIMITATIONS</h3>
              </div>
              <ul className="matrix-list">
                <li><strong>No Warranty:</strong> The software is provided &quot;as is&quot; without warranty of any kind.</li>
                <li><strong>No Liability:</strong> Authors and contributors are not liable for any claim, damages, or other liability.</li>
              </ul>
            </div>
          </div>
        </section>

        <article className="license-copy">
          <div className="license-block-header">
            <div>
              <span className="license-block-eyebrow">CANONICAL TEXT</span>
              <h2>Standard MIT License</h2>
            </div>
            <LicenseCopyButton text={licenseText} />
          </div>

          <pre className="code-block license-pre">
            <code>{licenseText}</code>
          </pre>

          <div className="license-actions">
            <a
              className="doc-action"
              href="https://github.com/Erebuzzz/fieldweaver/blob/main/LICENSE"
              target="_blank"
              rel="noreferrer"
            >
              View repository license file <span aria-hidden="true">↗</span>
            </a>
          </div>
        </article>
      </main>
    </DocumentFrame>
  );
}
