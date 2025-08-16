import { useState } from "react";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [feedback, setFeedback] = useState<string[]>([]);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(
        "http://localhost:8000/videos/analyze-video/",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!res.ok) {
        console.error("Upload failed:", res.statusText);
        setUploading(false);
        return;
      }

      const data = await res.json();

      // Set feedback array and video URL
      setFeedback(data.feedback || []);
      // For previewing, create an object URL from the uploaded file
      setVideoUrl(URL.createObjectURL(file));
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold">FormAI Upload</h1>

      {/* File input */}
      <input
        type="file"
        accept="video/*"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="my-4"
      />

      {/* Upload button */}
      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        {uploading ? "Uploading..." : "Upload Video"}
      </button>

      {/* Show uploaded video */}
      {videoUrl && (
        <div className="mt-6">
          <h2 className="text-xl font-semibold">Uploaded Video</h2>
          <video src={videoUrl} controls className="mt-2 w-full max-w-lg" />
        </div>
      )}

      {/* Show feedback */}
      {feedback.length > 0 && (
        <div className="mt-6">
          <h2 className="text-xl font-semibold">Form Feedback</h2>
          <ul className="mt-2 list-disc pl-6">
            {feedback.map((fb, index) => (
              <li key={index}>{fb}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
