import React, { useState } from 'react';
import './UploadForm.css';

const UploadForm = () => {
  const [imageUrl, setImageUrl] = useState('');
  const [message, setMessage] = useState('');
  const [publicUrl, setPublicUrl] = useState('');

  const handleUpload = async (event) => {
    event.preventDefault();

    try {
      const response = await fetch('http://34.67.21.176:81//upload-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image_url: imageUrl }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('File uploaded successfully!');
        setPublicUrl(data.public_url);
      } else {
        setMessage(`Error: ${data.error}`);
      }
    } catch (error) {
      setMessage(`Error: ${error.message}`);
    }
  };

  return (
    <div className="app-container">
      <h1>Image Upload</h1>
      <form onSubmit={handleUpload}>
        <input
          type="text"
          placeholder="Enter image URL"
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
          required
        />
        <button type="submit">Upload</button>
      </form>
      {message && <p className="message">{message}</p>}
      {publicUrl && (
        <div className="uploaded-image">
          <h3>Uploaded Image URL:</h3>
          <p>Public URL: <a href={publicUrl}>{publicUrl}</a></p>
        </div>
      )}
    </div>
  );
};

export default UploadForm;
