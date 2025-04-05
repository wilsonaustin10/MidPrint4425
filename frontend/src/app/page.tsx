'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import OnboardingGuide from '@/components/OnboardingGuide'
import { useSession } from '@/lib/SessionContext'
import RecentTasksList from '@/components/RecentTasksList'
import RecentUrlsList from '@/components/RecentUrlsList'
import { useRouter } from 'next/navigation'

export default function Home() {
  const { hasCompletedOnboarding } = useSession();
  const [showOnboarding, setShowOnboarding] = useState(false);
  const router = useRouter();

  // Show onboarding guide for new users
  useEffect(() => {
    setShowOnboarding(!hasCompletedOnboarding);
  }, [hasCompletedOnboarding]);

  const handleSelectTask = (taskDescription: string) => {
    // Navigate to chat with the task pre-filled
    router.push(`/chat?task=${encodeURIComponent(taskDescription)}`);
  };

  const handleSelectUrl = (url: string) => {
    // Navigate to browser with the URL pre-filled
    router.push(`/browser?url=${encodeURIComponent(url)}`);
  };

  return (
    <>
      <div className="flex flex-col items-center justify-center min-h-screen py-2">
        <main className="flex flex-col items-center justify-center w-full flex-1 px-4 md:px-20 text-center">
          <h1 className="text-4xl md:text-6xl font-bold">
            Welcome to{' '}
            <span className="text-blue-600">
              MidPrint
            </span>
          </h1>

          <p className="mt-3 text-xl md:text-2xl">
            AI-powered browser automation agent
          </p>

          <div className="flex flex-wrap items-center justify-around max-w-4xl mt-6 sm:w-full">
            <Link href="/chat" 
                  className="p-6 mt-6 text-left border w-full md:w-96 rounded-xl hover:text-blue-600 focus:text-blue-600 hover:border-blue-600 transition-colors">
              <h3 className="text-2xl font-bold">Chat Interface &rarr;</h3>
              <p className="mt-4 text-xl">
                Start giving instructions to the browser agent
              </p>
            </Link>

            <Link href="/browser"
                  className="p-6 mt-6 text-left border w-full md:w-96 rounded-xl hover:text-blue-600 focus:text-blue-600 hover:border-blue-600 transition-colors">
              <h3 className="text-2xl font-bold">Browser View &rarr;</h3>
              <p className="mt-4 text-xl">
                View the embedded browser and watch actions
              </p>
            </Link>
          </div>

          {/* Recent Activity Section */}
          <div className="w-full max-w-4xl mt-12 grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <RecentTasksList onSelectTask={handleSelectTask} />
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <RecentUrlsList onSelectUrl={handleSelectUrl} />
            </div>
          </div>
        </main>

        <footer className="flex items-center justify-center w-full h-24 border-t mt-8">
          <p>
            MidPrint Browser Agent
          </p>
        </footer>
      </div>

      {/* Onboarding Guide */}
      <OnboardingGuide 
        defaultOpen={showOnboarding}
        onComplete={() => setShowOnboarding(false)}
      />
    </>
  )
} 