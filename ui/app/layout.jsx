export const metadata = {
  title: "Mercator",
  description: "Trading made human",
  generator: "v0.dev",
  icons: {
    icon: '/mercator-symbol.svg',
    apple: '/mercator-symbol.svg',
  },
}

import ClientLayout from "./clientLayout"

export default function RootLayout({ children }) {
  return <ClientLayout>{children}</ClientLayout>
}

import "./globals.css"
