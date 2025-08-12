import { useState } from "react";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("http://localhost:8000/videos/upload", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    console.log(data);
    setUploading(false);
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold">FormAI Upload</h1>
      <input
        type="file"
        accept="video/*"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="my-4"
      />
      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        {uploading ? "Uploading..." : "Upload Video"}
      </button>
    </div>
  );
}
