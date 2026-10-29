import type { Metadata } from "next";

import { DocumentFrame } from "@/components/site-chrome";

export const metadata: Metadata = {
  title: "MIT License",
  description: "License terms for the FieldWeaver project.",
};

export default function LicensePage() {
  return (
    <DocumentFrame active="license">
      <main className="document-main policy-main license-main">
        <section className="document-hero policy-hero">
          <p className="eyebrow"><span className="eyebrow-mark" aria-hidden="true" />PROJECT TERMS / 01</p>
          <h1>Built to be<br /><em>used and studied.</em></h1>
          <p className="document-lede">FieldWeaver&apos;s source code is released under the MIT License.</p>
          <div className="doc-hero-meta"><span>MIT</span><span>2026 FIELDWEAVER CONTRIBUTORS</span></div>
        </section>

        <article className="license-copy">
          <h2>MIT License</h2>
          <p>Copyright (c) 2026 FieldWeaver contributors</p>
          <p>Permission is hereby granted, free of charge, to any person obtaining a copy
            of this software and associated documentation files (the &quot;Software&quot;), to deal
            in the Software without restriction, including without limitation the rights
            to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
            copies of the Software, and to permit persons to whom the Software is
            furnished to do so, subject to the following conditions:</p>
          <p>The above copyright notice and this permission notice shall be included in all
            copies or substantial portions of the Software.</p>
          <p>THE SOFTWARE IS PROVIDED &quot;AS IS&quot;, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
            IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
            FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
            AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
            LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
            OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
            SOFTWARE.</p>
          <a className="doc-action" href="https://github.com/Erebuzzz/fieldweaver/blob/main/LICENSE" target="_blank" rel="noreferrer">View the repository license file <span aria-hidden="true">↗</span></a>
        </article>
      </main>
    </DocumentFrame>
  );
}
