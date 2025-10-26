import { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

export default function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [isAndroid, setIsAndroid] = useState(false);

  useEffect(() => {
    // Check if already installed (running as standalone app)
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches
      || window.navigator.standalone
      || document.referrer.includes('android-app://');

    if (isStandalone) {
      return; // Don't show prompt if already installed
    }

    // Check if user has dismissed the prompt before
    const hasSeenPrompt = localStorage.getItem('installPromptDismissed');
    if (hasSeenPrompt) {
      return;
    }

    // Detect platform
    const userAgent = window.navigator.userAgent.toLowerCase();
    const iOS = /iphone|ipad|ipod/.test(userAgent);
    const android = /android/.test(userAgent);

    setIsIOS(iOS);
    setIsAndroid(android);

    // Only show on mobile devices
    if (!iOS && !android) {
      return;
    }

    // For Android: Listen for beforeinstallprompt event
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // For iOS: Show instructions after a delay
    if (iOS) {
      const timer = setTimeout(() => {
        setShowPrompt(true);
      }, 3000); // Show after 3 seconds

      return () => {
        clearTimeout(timer);
        window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      };
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  const handleInstallClick = async () => {
    if (deferredPrompt) {
      // Android: Show the install prompt
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;

      if (outcome === 'accepted') {
        console.log('User accepted the install prompt');
      }

      setDeferredPrompt(null);
      setShowPrompt(false);
      localStorage.setItem('installPromptDismissed', 'true');
    }
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('installPromptDismissed', 'true');
  };

  if (!showPrompt) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:max-w-md z-50 animate-slide-up">
      <div className="bg-white rounded-lg shadow-2xl border border-gray-200 p-4">
        {/* Close button */}
        <button
          onClick={handleDismiss}
          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Dismiss"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>

        {/* Content */}
        <div className="flex items-start gap-3 pr-8">
          {/* App Icon */}
          <div className="flex-shrink-0">
            <img
              src="/icon-192.png"
              alt="Ruth App"
              className="w-12 h-12 rounded-lg"
            />
          </div>

          {/* Text Content */}
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              Install Ruth
            </h3>

            {isAndroid && deferredPrompt ? (
              <>
                <p className="text-sm text-gray-600 mb-3">
                  Add Ruth to your home screen for quick access and a better experience.
                </p>
                <button
                  onClick={handleInstallClick}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium text-sm transition-colors"
                >
                  Add to Home Screen
                </button>
              </>
            ) : isIOS ? (
              <>
                <p className="text-sm text-gray-600 mb-2">
                  Install this app on your device:
                </p>
                <ol className="text-xs text-gray-600 space-y-1 ml-4 list-decimal">
                  <li>Tap the Share button <span className="inline-block">⎙</span> in Safari</li>
                  <li>Select "Add to Home Screen"</li>
                  <li>Tap "Add" to confirm</li>
                </ol>
              </>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
