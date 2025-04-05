import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClientProviders } from '@/lib/ClientProviders'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'MidPrint - Browser Automation Agent',
  description: 'AI-powered browser automation agent that performs tasks using natural language instructions',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ClientProviders>
          <main className="min-h-screen bg-gray-50">
            {children}
          </main>
        </ClientProviders>
      </body>
    </html>
  )
} 