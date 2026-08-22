import React, { useRef, useEffect, useState } from 'react';
import landingVideo from '../assets/landing_video.mp4';

export default function LandingPage({ onProceedToLogin }) {
  const videoRef = useRef(null);
  const [isFadingOut, setIsFadingOut] = useState(false);

  const handleTransition = () => {
    if (isFadingOut) return;
    setIsFadingOut(true);
    setTimeout(() => {
      onProceedToLogin();
    }, 700);
  };

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.play().catch(err => {
        console.warn("Autoplay fallback:", err);
      });
    }
  }, []);

  return (
    <div
      onClick={handleTransition}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: '#000',
        zIndex: 999999,
        cursor: 'pointer',
        overflow: 'hidden',
        opacity: isFadingOut ? 0 : 1,
        transition: 'opacity 0.7s ease-in-out',
        pointerEvents: isFadingOut ? 'none' : 'auto'
      }}
    >
      <video
        ref={videoRef}
        src={landingVideo}
        autoPlay
        muted
        playsInline
        onEnded={handleTransition}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover'
        }}
      />
    </div>
  );
}
