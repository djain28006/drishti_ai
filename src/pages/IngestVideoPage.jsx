import React, { useState, useRef } from 'react';
import { UploadCloud, Camera, Video, AlertCircle } from 'lucide-react';

export default function IngestVideoPage({ apiBase = '', onStartJob, setCurrentPage }) {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [recording, setRecording] = useState(false);
  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const handleFileDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const res = await fetch(`${apiBase}/api/analyze`, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        if (data.job_id && onStartJob) {
          onStartJob(data.job_id);
          setCurrentPage('processing');
        }
      }
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
    }
  };

  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'video/webm' });
        const file = new File([blob], "live_surveillance.webm", { type: 'video/webm' });
        setSelectedFile(file);
        // Stop stream
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setRecording(true);
    } catch (err) {
      alert("Could not access camera: " + err.message);
    }
  };

  const stopWebcam = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  return (
    <div className="content-area">
      <div>
        <h1 className="page-title">Ingest CCTV Surveillance Video</h1>
        <p className="page-subtitle">Upload examination video file or trigger live webcam stream for offline forensic segmentation.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* File Drag and Drop */}
        <div 
          className="card" 
          style={{
            border: dragOver ? '2px dashed var(--accent-cyan)' : '2px dashed var(--border-color)',
            background: dragOver ? 'var(--accent-cyan-dim)' : 'var(--bg-card)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '40px 20px',
            textAlign: 'center',
            cursor: 'pointer'
          }}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleFileDrop}
        >
          <UploadCloud size={48} style={{ color: 'var(--accent-cyan)', marginBottom: '14px' }} />
          <div style={{ fontSize: '15px', fontWeight: '700', color: '#fff', marginBottom: '4px' }}>
            Drag & Drop Examination Video Here
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Supports MP4, WEBM, MOV, AVI (Up to 4K resolution)
          </div>

          <label className="btn-new-investigation" style={{ width: 'auto', display: 'inline-flex', cursor: 'pointer' }}>
            <Video size={14} /> Browse Video File
            <input type="file" accept="video/*" onChange={handleFileSelect} style={{ display: 'none' }} />
          </label>

          {selectedFile && (
            <div style={{ marginTop: '16px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--accent-cyan)' }}>
              Selected: <strong>{selectedFile.name}</strong> ({ (selectedFile.size / 1024 / 1024).toFixed(2) } MB)
            </div>
          )}

          {selectedFile && (
            <button 
              className="btn-new-investigation" 
              style={{ marginTop: '14px', width: '80%' }}
              onClick={handleUploadSubmit}
              disabled={uploading}
            >
              {uploading ? 'Ingesting Video...' : 'Start Forensic Analysis Pipeline'}
            </button>
          )}
        </div>

        {/* Live Camera Recording */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <Camera size={36} style={{ color: 'var(--accent-cyan)', marginBottom: '12px' }} />
          <div style={{ fontSize: '15px', fontWeight: '700', color: '#fff', marginBottom: '4px' }}>
            Live Feed Recording
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '14px' }}>
            Record webcam video clip to run spatial baseline segmentation.
          </div>

          <div style={{ width: '100%', height: '180px', background: '#000', borderRadius: '6px', overflow: 'hidden', marginBottom: '14px' }}>
            <video ref={videoRef} autoPlay muted style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </div>

          {!recording ? (
            <button className="btn-new-investigation" style={{ width: 'auto' }} onClick={startWebcam}>
              <Camera size={14} /> Start Camera Recording
            </button>
          ) : (
            <button className="btn-new-investigation" style={{ width: 'auto', background: 'var(--status-critical)' }} onClick={stopWebcam}>
              Stop & Use Recorded Clip
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
