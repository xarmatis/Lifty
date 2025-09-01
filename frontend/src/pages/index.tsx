import { useState, useEffect } from "react";
import { Upload, Loader2, Video, MessageSquare } from "lucide-react";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [feedback, setFeedback] = useState<any>([]);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [selectedExercise, setSelectedExercise] = useState<string>('squat');

  // Cleanup function to revoke old video URLs
  const cleanupVideoUrl = (url: string | null) => {
    if (url && url.startsWith('blob:')) {
      URL.revokeObjectURL(url);
    }
  };

  // Cleanup video URL when component unmounts
  useEffect(() => {
    return () => {
      if (videoUrl) {
        cleanupVideoUrl(videoUrl);
      }
    };
  }, [videoUrl]);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(0);

    // Simulate progress during upload and analysis
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) return 90; // Cap at 90% until we get response
        return Math.min(90, prev + Math.random() * 15); // Ensure we don't exceed 90%
      });
    }, 200);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("exercise_type", selectedExercise);

    try {
      const res = await fetch("http://localhost:8000/videos/analyze-video/", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        console.error("Upload failed:", res.statusText);
        setUploading(false);
        setProgress(0);
        clearInterval(progressInterval);
        return;
      }

      const data = await res.json();
      console.log('Backend response:', data);
      setFeedback(data || []);
      
      // Create video URL and add extensive debugging
      const videoUrl = URL.createObjectURL(file);
      console.log('=== VIDEO DEBUG INFO ===');
      console.log('File object:', file);
      console.log('File name:', file.name);
      console.log('File type:', file.type);
      console.log('File size:', file.size, 'bytes');
      console.log('File lastModified:', new Date(file.lastModified).toISOString());
      console.log('Created video URL:', videoUrl);
      console.log('URL object type:', typeof videoUrl);
      console.log('URL starts with blob:', videoUrl.startsWith('blob:'));
      
      // Test if the file is actually readable
      const reader = new FileReader();
      reader.onload = () => console.log('FileReader success - file is readable');
      reader.onerror = () => console.log('FileReader error - file is not readable');
      reader.readAsArrayBuffer(file.slice(0, 1024)); // Read first 1KB
      
      setVideoUrl(videoUrl);
      
      // Complete the progress
      setProgress(100);
      setTimeout(() => setProgress(0), 1000); // Reset after 1 second
    } catch (err) {
      console.error("Upload failed:", err);
      setProgress(0);
    } finally {
      setUploading(false);
      clearInterval(progressInterval);
    }
  };

  const containerStyle = {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '20px'
  };

  const cardStyle = {
    width: '100%',
    maxWidth: '600px',
    background: 'rgba(255, 255, 255, 0.95)',
    borderRadius: '20px',
    boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
    padding: '40px',
    textAlign: 'center' as const
  };

  const titleStyle = {
    fontSize: '48px',
    fontWeight: 'bold',
    background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
    WebkitBackgroundClip: 'text' as const,
    WebkitTextFillColor: 'transparent' as const,
    marginBottom: '10px'
  };

  const uploadAreaStyle = {
    border: '2px dashed #cbd5e1',
    borderRadius: '16px',
    padding: '40px 20px',
    marginBottom: '24px',
    background: 'linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%)',
    cursor: 'pointer'
  };

  const buttonStyle = {
    width: '100%',
    padding: '16px 32px',
    background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '16px',
    fontSize: '18px',
    fontWeight: '600',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px'
  };

  const sectionStyle = {
    marginTop: '40px',
    padding: '24px',
    background: 'linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%)',
    borderRadius: '16px',
    border: '1px solid #e2e8f0'
  };

  const videoStyle = {
    width: '100%',
    maxWidth: '400px',
    maxHeight: '250px',
    borderRadius: '12px',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)'
  };

  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        {/* Header */}
        <div style={{ marginBottom: '40px' }}>
          <h1 style={titleStyle}>Lifty</h1>
          <p style={{ color: '#64748b', fontSize: '18px' }}>AI-Powered Form Analysis</p>
        </div>

        {/* Upload section */}
        <div style={uploadAreaStyle}>
          <div style={{
            width: '64px',
            height: '64px',
            background: '#dbeafe',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px',
            color: '#2563eb'
          }}>
            <Upload size={32} />
          </div>
          <p style={{ color: '#334155', fontSize: '18px', fontWeight: '500', marginBottom: '12px' }}>
            {file ? file.name : "Drag & drop a video or click to select"}
          </p>
          <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '20px' }}>
            Supports MP4, AVI, MOV, and other video formats
          </p>
          <input
            type="file"
            accept="video/*,.mp4,.mov,.avi,.MP4,.MOV,.AVI"
            onChange={(e) => {
              const newFile = e.target.files?.[0] || null;
              
              // Debug file information
              if (newFile) {
                console.log('File selected:', newFile.name);
                console.log('File type:', newFile.type);
                console.log('File size:', newFile.size);
              }
              
              // Clean up previous video URL before setting new file
              if (videoUrl) {
                cleanupVideoUrl(videoUrl);
              }
              
              setFile(newFile);
              
              // Clear previous video and feedback when a new file is selected
              if (newFile) {
                setVideoUrl(null);
                setFeedback([]);
                setProgress(0);
              }
            }}
            style={{ display: 'none' }}
            id="fileInput"
          />
          <label htmlFor="fileInput" style={{
            display: 'inline-block',
            padding: '12px 24px',
            background: 'white',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            color: '#334155',
            fontWeight: '500',
            cursor: 'pointer'
          }}>
            Browse Files
          </label>
        </div>

        {/* Exercise Selection */}
        <div style={{
          marginBottom: '24px',
          textAlign: 'left'
        }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontSize: '16px',
            fontWeight: '500',
            color: '#374151'
          }}>
            Select Exercise Type:
          </label>
          <select
            value={selectedExercise}
            onChange={(e) => {
              setSelectedExercise(e.target.value);
              // Clear previous feedback when exercise type changes
              setFeedback([]);
              setVideoUrl(null);
              setProgress(0);
            }}
            style={{
              width: '100%',
              padding: '12px 16px',
              border: '1px solid #e2e8f0',
              borderRadius: '12px',
              fontSize: '16px',
              background: 'white',
              color: '#374151'
            }}
          >
            <option value="squat">Squat</option>
            <option value="deadlift">Deadlift</option>
            <option value="pushup">Push-up</option>
            <option value="plank">Plank</option>
            <option value="lunge">Lunge</option>
          </select>
        </div>

        {/* Upload button */}
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          style={{
            ...buttonStyle,
            opacity: (!file || uploading) ? 0.5 : 1,
            cursor: (!file || uploading) ? 'not-allowed' : 'pointer',
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          {uploading ? (
            <>
              <Video size={20} />
              Analyzing Video... {Math.round(progress)}%
              {/* Progress bar overlay */}
              <div style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                height: '4px',
                background: 'rgba(255, 255, 255, 0.3)',
                width: '100%',
                borderRadius: '0 0 16px 16px'
              }}>
                <div style={{
                  height: '100%',
                  background: 'rgba(255, 255, 255, 0.8)',
                  width: `${progress}%`,
                  transition: 'width 0.3s ease',
                  borderRadius: '0 0 16px 16px'
                }} />
              </div>
            </>
          ) : (
            <>
              <Video size={20} />
              Analyze Video
            </>
          )}
        </button>

        {/* Show uploaded video */}
        {videoUrl && (
          <div style={sectionStyle}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              marginBottom: '20px',
              color: '#2563eb'
            }}>
              <Video size={24} />
              <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#1e293b', margin: 0 }}>
                Uploaded Video
              </h2>
            </div>
            <div style={{ display: 'flex', justifyContent: 'center' }}>
                             <video 
                 src={videoUrl} 
                 controls 
                 preload="metadata"
                 style={videoStyle}
                 crossOrigin="anonymous"
                 muted
                 playsInline
                 onError={(e) => {
                   const video = e.target as HTMLVideoElement;
                   console.error('Video error details:');
                   console.error('- Error code:', video.error?.code);
                   console.error('- Error message:', video.error?.message);
                   console.error('- Video src:', video.src);
                   console.error('- Video readyState:', video.readyState);
                   console.error('- Video networkState:', video.networkState);
                   
                   // Try to recover from timestamp errors
                   if (video.error?.code === 4 && video.error?.message?.includes('timestamp')) {
                     console.log('Attempting to recover from timestamp error...');
                     // Remove and re-add the video element to force a fresh load
                     const videoContainer = video.parentElement;
                     if (videoContainer) {
                       video.remove();
                       const newVideo = document.createElement('video');
                       newVideo.src = videoUrl;
                       newVideo.controls = true;
                       newVideo.preload = 'metadata';
                       newVideo.style.cssText = Object.entries(videoStyle).map(([k, v]) => `${k}: ${v}`).join(';');
                       newVideo.crossOrigin = 'anonymous';
                       newVideo.muted = true;
                       newVideo.playsInline = true;
                       
                       // Add error handling to the new video
                       newVideo.onerror = video.onerror;
                       newVideo.onloadstart = video.onloadstart;
                       newVideo.onloadedmetadata = video.onloadedmetadata;
                       newVideo.oncanplay = video.oncanplay;
                       newVideo.onloadeddata = video.onloadeddata;
                       
                       videoContainer.appendChild(newVideo);
                     }
                   }
                 }}
                 onLoadStart={() => console.log('Video load started')}
                 onLoadedMetadata={() => console.log('Video metadata loaded')}
                 onCanPlay={() => console.log('Video can play')}
                 onLoadedData={() => console.log('Video data loaded')}
               />
            </div>
          </div>
        )}

        {/* Show feedback */}
        {feedback && (feedback.feedback_per_rep || (Array.isArray(feedback) && feedback.length > 0)) && (
          <div style={sectionStyle}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              marginBottom: '20px',
              color: '#2563eb'
            }}>
              <MessageSquare size={24} />
                             <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#1e293b', margin: 0 }}>
                 {selectedExercise.charAt(0).toUpperCase() + selectedExercise.slice(1)} Analysis
               </h2>
            </div>
            
                         {/* Exercise Summary */}
             {feedback && (
              <div style={{
                background: 'rgba(255, 255, 255, 0.8)',
                borderRadius: '12px',
                padding: '20px',
                marginBottom: '20px',
                border: '1px solid #e2e8f0',
                textAlign: 'center'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-around',
                  alignItems: 'center',
                  marginBottom: '16px'
                }}>
                  <div>
                    <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Exercise</p>
                                         <p style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#1e293b' }}>
                       {selectedExercise.charAt(0).toUpperCase() + selectedExercise.slice(1)}
                     </p>
                  </div>
                  <div>
                    <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Reps</p>
                    <p style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#1e293b' }}>
                      {feedback.reps_detected || 0}
                    </p>
                  </div>
                  <div>
                    <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Score</p>
                    <p style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#1e293b' }}>
                      {feedback.overall_score || 0}/100
                    </p>
                  </div>
                </div>
                
                {/* Overall Recommendations */}
                {feedback.summary?.recommendations && (
                  <div style={{ textAlign: 'left' }}>
                    <p style={{ margin: '0 0 8px 0', fontSize: '14px', fontWeight: '500', color: '#374151' }}>
                      Overall Recommendations:
                    </p>
                    {feedback.summary.recommendations.map((rec: string, index: number) => (
                      <p key={index} style={{ 
                        margin: '4px 0', 
                        fontSize: '14px', 
                        color: '#64748b',
                        paddingLeft: '16px'
                      }}>
                        • {rec}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {/* Detailed Feedback Per Rep */}
            <div style={{ maxWidth: '600px', margin: '0 auto' }}>
              {feedback.feedback_per_rep ? (
                feedback.feedback_per_rep.map((rep: any, index: number) => (
                  <div key={index} style={{
                    background: 'rgba(255, 255, 255, 0.8)',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '16px',
                    border: '1px solid #e2e8f0'
                  }}>
                    {/* Rep Header */}
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '12px',
                      paddingBottom: '8px',
                      borderBottom: '1px solid #e2e8f0'
                    }}>
                      <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#1e293b' }}>
                        Rep {rep.rep}
                      </h3>
                      <div style={{
                        padding: '4px 12px',
                        borderRadius: '20px',
                        background: rep.score >= 80 ? '#dcfce7' : rep.score >= 60 ? '#fef3c7' : '#fee2e2',
                        color: rep.score >= 80 ? '#166534' : rep.score >= 60 ? '#92400e' : '#dc2626',
                        fontSize: '14px',
                        fontWeight: '500'
                      }}>
                        {rep.score}/100
                      </div>
                    </div>
                    
                    {/* Feedback Points */}
                    <div style={{ marginBottom: '12px' }}>
                                             {rep.feedback.map((fb: string, fbIndex: number) => (
                        <p key={fbIndex} style={{
                          margin: '8px 0',
                          fontSize: '14px',
                          color: '#374151',
                          lineHeight: 1.5,
                          paddingLeft: '16px',
                          position: 'relative'
                        }}>
                          <span style={{
                            position: 'absolute',
                            left: '0',
                            top: '8px',
                            width: '6px',
                            height: '6px',
                            background: '#10b981',
                            borderRadius: '50%'
                          }}></span>
                          {fb}
                        </p>
                      ))}
                    </div>
                    
                    {/* Metrics */}
                    {rep.metrics && Object.keys(rep.metrics).length > 0 && (
                      <div style={{
                        background: '#f8fafc',
                        borderRadius: '8px',
                        padding: '12px',
                        fontSize: '12px',
                        color: '#64748b'
                      }}>
                        <p style={{ margin: '0 0 8px 0', fontWeight: '500' }}>Metrics:</p>
                        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                          {Object.entries(rep.metrics).map(([key, value]) => (
                            <span key={key}>
                              {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}: {String(value)}°
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                // Fallback for old format or simple feedback
                                 feedback.map((fb: string, index: number) => (
                  <div key={index} style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '16px 20px',
                    background: 'rgba(255, 255, 255, 0.7)',
                    borderRadius: '12px',
                    marginBottom: '12px',
                    border: '1px solid #d1fae5',
                    textAlign: 'left' as const
                  }}>
                                         <div style={{
                       width: '8px',
                       height: '8px',
                       background: '#10b981',
                       borderRadius: '50%',
                       marginTop: '8px',
                       flexShrink: 0
                     }}></div>
                     <p style={{ margin: 0, color: '#374151', lineHeight: 1.6 }}>{fb}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
