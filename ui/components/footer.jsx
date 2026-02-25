export default function Footer() {
  return (
    <footer className="py-8 px-4 border-t border-border/40">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <img 
              src="/mercator-symbol.svg" 
              alt="Mercator" 
              className="h-8 w-8 opacity-70"
            />
            <span className="text-sm text-muted-foreground">
              © 2025 Mercator. All rights reserved.
            </span>
          </div>
          <div className="flex gap-6">
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Privacy
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Terms
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Contact
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
