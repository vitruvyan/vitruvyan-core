# Vitruvyan UI - Roadmap & Progress Tracker
**Last Updated**: November 22, 2025  
**Branch**: `feature/landing-chat-ux`

---

## ✅ Phase 1: ChatGPT-Style Landing Experience (COMPLETED)

### 🎨 Visual Design
- [x] **Ticker badges** with rounded pills above input
- [x] **Color scheme** changed to warm dark gray (#333333) site-wide
- [x] **ChatGPT-style clean messages** (no borders, no shadows)
- [x] **Alternating backgrounds** (white for user, gray-50 for AI)
- [x] **Minimal header** (logo + login button, no menu hamburger)
- [x] **Clean footer** maintained

### 🎬 Animations & Transitions
- [x] **Hero fade-out** animation (opacity + scale-95) on submit
- [x] **Chat slide-in** with custom `slideDown` keyframe (500ms ease-out)
- [x] **Submit button morph** (text disappears, only arrow icon remains)
- [x] **Greeting & carousel fade** during transition
- [x] **Smooth state management** (400ms transition delay)

### 🧹 Cleanup
- [x] **Removed modal popup** for chat (now inline)
- [x] **Removed PaywallModal** (no query limits)
- [x] **Removed chat header** "Chat with Mercator"
- [x] **Removed greeting message** "Hi! I'm Mercator..."
- [x] **Removed Dev Mode banner**
- [x] **Removed sidebar**, old pages (portfolio, pricing, manifesto)

### 📁 Files Modified
\`\`\`
app/page.jsx                  - Transition state management
app/clientLayout.jsx          - Minimal layout (Header+Footer only)
components/hero-landing.jsx   - Fade animations + button morph
components/header.jsx         - Removed menu toggle, simplified
components/chat.jsx           - Inline rendering, clean style
tailwind.config.js            - slideDown keyframe + accent color
\`\`\`

**Git Commit**: `2ce0e43` - "✨ ChatGPT-style UI complete: clean layout + smooth animations"

---

## 🔄 Phase 2: Backend Integration (NEXT)

### 🔌 API Connection
- [ ] Connect chat to Vitruvyan backend API (port 8004)
- [ ] Test real queries with Neural Engine
- [ ] Verify ticker extraction accuracy
- [ ] Test sentiment analysis integration
- [ ] Handle API errors gracefully

### 🧪 Testing
- [ ] Test with actual backend responses
- [ ] Verify VEE (explainability engine) integration
- [ ] Test multi-ticker queries
- [ ] Test Italian language queries
- [ ] Performance testing (response time)

### 📊 Data Display
- [ ] Format numerical analysis properly
- [ ] Display trend/momentum scores
- [ ] Show sentiment indicators
- [ ] Add technical details expandable sections

---

## 📱 Phase 3: Responsive Design

### Mobile (< 640px)
- [ ] Optimize chat layout for mobile
- [ ] Touch-friendly input area
- [ ] Adjust carousel scrolling
- [ ] Test on iOS Safari
- [ ] Test on Android Chrome

### Tablet (640-1024px)
- [ ] Optimize middle-range screens
- [ ] Adjust max-width constraints
- [ ] Test landscape mode

---

## 🎭 Phase 4: Advanced UX

### Animations
- [ ] Reverse animation (chat → landing with back button)
- [ ] Loading skeleton during API calls
- [ ] Smooth scroll to new messages
- [ ] Message appearance animation (fade-in)

### Interactions
- [ ] Copy message to clipboard
- [ ] Share conversation link
- [ ] Clear chat history button
- [ ] Export conversation as PDF

### Smart Features
- [ ] Typing indicator with real-time updates
- [ ] Auto-scroll to bottom on new message
- [ ] Keyboard shortcuts (Ctrl+K to focus input)
- [ ] Voice input integration

---

## ♿ Phase 5: Accessibility

- [ ] Screen reader support (ARIA labels)
- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] Focus management during transitions
- [ ] High contrast mode
- [ ] Reduced motion mode (prefers-reduced-motion)

---

## 🧪 Phase 6: Testing & Quality

### E2E Testing (Playwright)
- [ ] Landing page load test
- [ ] Submit query flow test
- [ ] Ticker autocomplete test
- [ ] Animation performance test

### Unit Tests (Jest + React Testing Library)
- [ ] HeroLanding component
- [ ] Chat component
- [ ] Header component
- [ ] Ticker detection logic

### Performance
- [ ] Lighthouse audit (target: 95+ score)
- [ ] Bundle size optimization
- [ ] Code splitting
- [ ] Image optimization

---

## 🚀 Phase 7: Production Deployment

- [ ] Environment variables setup
- [ ] Build optimization
- [ ] CDN configuration
- [ ] Analytics integration (Google Analytics / Plausible)
- [ ] Error tracking (Sentry)
- [ ] A/B testing setup

---

## 🐛 Known Issues / Tech Debt

- [ ] None currently - fresh refactor! 🎉

---

## 💡 Future Ideas (Backlog)

- [ ] Dark mode toggle
- [ ] Conversation history (saved chats)
- [ ] Multi-language UI (IT/EN/ES toggle)
- [ ] Chat export (JSON, PDF, TXT)
- [ ] Inline chart visualizations
- [ ] Real-time market data ticker
- [ ] AI agent personality customization
- [ ] Collaborative chat (share with others)

---

## 📝 Notes

**Current Status**: Phase 1 complete! UI is production-ready visually.  
**Next Priority**: Backend integration (Phase 2)  
**Blockers**: None  
**Dependencies**: Backend API at http://161.97.140.157:8004

---

**Ready for next task! 🚀**
