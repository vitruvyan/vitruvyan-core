"use client"

export default function ManifestoPage() {
  return (
    <div className="flex flex-1 bg-gray-100">
      <div className="flex-1 overflow-y-auto p-6 lg:p-8">
        <div className="mx-auto max-w-4xl">
          {/* Header */}
          <div className="mb-12 text-center">
            <h1 className="font-barlow-condensed text-4xl font-bold text-gray-900 lg:text-5xl uppercase tracking-wide">
              Mercator Manifesto
            </h1>
            <p className="mt-4 font-ibm-plex-sans text-xl text-gray-600 lg:text-2xl">Trading made human.</p>
          </div>

          {/* Introduction */}
          <div className="mb-12 rounded-xl bg-white p-8 shadow-sm ring-1 ring-gray-200">
            <p className="font-nunito text-lg leading-relaxed text-gray-700">
              For too long, trading has been the domain of a few: complex, opaque, built for machines rather than
              people.
              <br />
              <span className="font-semibold text-gray-900">
                Mercator was created to turn this paradigm upside down.
              </span>
            </p>
          </div>

          {/* Principles Section */}
          <div className="mb-12">
            <h2 className="mb-8 flex items-center font-ibm-plex-sans text-3xl font-semibold text-gray-900">
              <span className="mr-3 text-2xl">🔑</span>
              Our Principles
            </h2>

            <div className="space-y-8">
              {/* Principle 1 */}
              <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
                <h3 className="mb-3 font-ibm-plex-sans text-xl font-semibold text-gray-900">
                  1. Democratizing trading
                </h3>
                <p className="font-nunito leading-relaxed text-gray-700">
                  Investing should not be a privilege reserved for experts or those with exclusive resources. Mercator
                  breaks down barriers, making trading understandable and accessible to everyone.
                </p>
              </div>

              {/* Principle 2 */}
              <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
                <h3 className="mb-3 font-ibm-plex-sans text-xl font-semibold text-gray-900">
                  2. Reverse-engineering finance
                </h3>
                <p className="font-nunito leading-relaxed text-gray-700">
                  We dismantle and rebuild market logic to make it transparent. No secret formulas, no "black boxes":
                  Mercator reveals and explains how and why every signal is generated.
                </p>
              </div>

              {/* Principle 3 */}
              <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
                <h3 className="mb-3 font-ibm-plex-sans text-xl font-semibold text-gray-900">3. User at the center</h3>
                <p className="font-nunito leading-relaxed text-gray-700">
                  Not algorithms that dictate choices, but a companion that listens, explains, and guides. The user does
                  not follow blindly — they decide with awareness.
                </p>
              </div>

              {/* Principle 4 */}
              <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
                <h3 className="mb-3 font-ibm-plex-sans text-xl font-semibold text-gray-900">4. Trading open to all</h3>
                <p className="font-nunito leading-relaxed text-gray-700">
                  From beginners to experts, Mercator speaks a human language. No dictionary of acronyms required: just
                  clarity, trust, and motivation.
                </p>
              </div>

              {/* Principle 5 */}
              <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
                <h3 className="mb-3 font-ibm-plex-sans text-xl font-semibold text-gray-900">
                  5. Explainability and trust
                </h3>
                <p className="font-nunito leading-relaxed text-gray-700">
                  Every BUY/SELL comes with a reason. Every risk is spelled out. Every strategy is motivated.
                  Transparency is our form of respect.
                </p>
              </div>

              {/* Principle 6 */}
              <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
                <h3 className="mb-3 font-ibm-plex-sans text-xl font-semibold text-gray-900">
                  6. Modularity and openness
                </h3>
                <p className="font-nunito leading-relaxed text-gray-700">
                  Mercator is not a closed product but an ecosystem. Composable agents, explainable tools, a community
                  building together. Strength lies not in a single algorithm but in an open architecture.
                </p>
              </div>
            </div>
          </div>

          {/* Promise Section */}
          <div className="mb-12">
            <h2 className="mb-8 flex items-center font-ibm-plex-sans text-3xl font-semibold text-gray-900">
              <span className="mr-3 text-2xl">🧭</span>
              Our Promise
            </h2>

            <div className="rounded-xl bg-gray-50 p-8 shadow-sm ring-1 ring-gray-200">
              <p className="font-nunito text-lg leading-relaxed text-gray-700">
                To reduce complexity, give back control, and transform trading into a clear, motivating, and human
                experience.
              </p>
              <p className="mt-4 font-nunito text-lg font-semibold leading-relaxed text-gray-900">
                Because the future of finance does not belong to machines — but to the people who know how to use them.
              </p>
            </div>
          </div>

          {/* Call to Action */}
          <div className="text-center">
            <div className="rounded-xl bg-white p-8 shadow-sm ring-1 ring-gray-200">
              <h3 className="mb-4 font-ibm-plex-sans text-2xl font-semibold text-gray-900">
                Ready to experience human trading?
              </h3>
              <p className="mb-6 font-nunito text-gray-600">
                Join us in revolutionizing the way people interact with financial markets.
              </p>
              <a
                href="/"
                className="inline-flex items-center rounded-lg bg-gray-900 px-6 py-3 font-nunito font-semibold text-white transition-colors hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              >
                Start Trading Human
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
