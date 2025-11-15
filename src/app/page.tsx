"use client";

import { useState, useRef, useCallback, useEffect } from 'react';
import { Upload, User, MapPin, FileText, Zap, Download, CheckCircle, Loader2 } from 'lucide-react';

interface ImagePreview {
  file: File;
  preview: string;
  id: string;
}

export default function Home() {
  const [text, setText] = useState('');
  const [teamMemberToken, setTeamMemberToken] = useState('mehdi');
  const [gpsLocation, setGpsLocation] = useState('usa');
  const [imagePreviews, setImagePreviews] = useState<ImagePreview[]>([]);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [processingStep, setProcessingStep] = useState<string>('');
  const [progressDots, setProgressDots] = useState<boolean[]>([false, false, false]);
  const [isAnimating, setIsAnimating] = useState(false);
  
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(true);
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [selectedMember, setSelectedMember] = useState('');
  const [showPasswordStep, setShowPasswordStep] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Check for saved session on component mount
  useEffect(() => {
    const savedSession = localStorage.getItem('happydeel_session');
    if (savedSession) {
      try {
        const sessionData = JSON.parse(savedSession);
        const now = new Date().getTime();
        const sessionExpiry = sessionData.expiry || 0;
        
        // Check if session is still valid (7 days)
        if (now < sessionExpiry) {
          setIsAuthenticated(true);
          setShowLoginModal(false);
          setTeamMemberToken(sessionData.memberId);
          setSelectedMember(sessionData.memberId);
        } else {
          // Session expired, clear it
          localStorage.removeItem('happydeel_session');
        }
      } catch (error) {
        // Invalid session data, clear it
        localStorage.removeItem('happydeel_session');
      }
    }
  }, []);

  // Team members list with individual passwords
  const teamMembers = [
    { id: 'mehdi', name: 'Mehdi', password: 'Localserver!!2' },
    { id: 'jebbar', name: 'Jebbar', password: 'JLocal!!2' },
    { id: 'abdo', name: 'Abdo', password: 'ALocal!!2' },
    { id: 'walid', name: 'Walid', password: 'Wlocal!!2' },
    { id: 'amine', name: 'Amine', password: 'AMLocal!!2' },
    { id: 'janah', name: 'Janah', password: 'JanLocal!!2' }
  ];

  // Authentication functions
  const handleMemberSelect = (memberId: string) => {
    setSelectedMember(memberId);
    setTeamMemberToken(memberId);
    setShowPasswordStep(true);
    setLoginError('');
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    
    const selectedMemberData = teamMembers.find(member => member.id === selectedMember);
    const correctPassword = selectedMemberData?.password || 'Localserver!!2';
    
    if (loginPassword === correctPassword) {
      // Save session to localStorage (7 days)
      const sessionData = {
        memberId: selectedMember,
        memberName: selectedMemberData?.name,
        loginTime: new Date().getTime(),
        expiry: new Date().getTime() + (7 * 24 * 60 * 60 * 1000) // 7 days
      };
      localStorage.setItem('happydeel_session', JSON.stringify(sessionData));
      
      // Track login event
      try {
        await fetch('/api/login_tracking', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: selectedMember,
            user_name: selectedMemberData?.name || selectedMember,
            ip_address: 'Unknown', // Will be detected server-side
            user_agent: navigator.userAgent
          })
        });
      } catch (error) {
        console.log('Failed to track login:', error);
        // Don't block login if tracking fails
      }
      
      setIsAuthenticated(true);
      setShowLoginModal(false);
    } else {
      setLoginError('Invalid password. Please try again.');
    }
  };

  const handleBackToMembers = () => {
    setShowPasswordStep(false);
    setSelectedMember('');
    setLoginPassword('');
    setLoginError('');
  };

  const handleLogout = () => {
    // Clear session from localStorage
    localStorage.removeItem('happydeel_session');
    
    setIsAuthenticated(false);
    setShowLoginModal(true);
    setShowPasswordStep(false);
    setSelectedMember('');
    setLoginPassword('');
    setLoginError('');
    // Clear all data on logout
    setText('');
    setImagePreviews([]);
    setDownloadUrl(null);
    setError(null);
  };

  // Cool progress animation
  const animateProgress = useCallback(() => {
    setIsAnimating(true);
    setProgressDots([false, false, false]);
    
    const steps = [
      { step: "Preparing files...", progress: 20, dot: 0 },
      { step: "Processing images...", progress: 50, dot: 1 },
      { step: "Adding EXIF data...", progress: 80, dot: 2 },
      { step: "Generating AI content...", progress: 95, dot: 2 },
      { step: "Finalizing...", progress: 100, dot: 2 }
    ];
    
    steps.forEach((step, index) => {
      setTimeout(() => {
        setProcessingStep(step.step);
        setUploadProgress(step.progress);
        
        if (step.dot !== undefined) {
          setProgressDots(prev => {
            const newDots = [...prev];
            newDots[step.dot] = true;
            return newDots;
          });
        }
        
        if (index === steps.length - 1) {
          setTimeout(() => {
            setIsAnimating(false);
          }, 500);
        }
      }, index * 800);
    });
  }, []);

  // Handle file selection and create previews
  const handleFiles = useCallback((files: FileList | null) => {
    if (!files) return;
    
    const newPreviews: ImagePreview[] = [];
    Array.from(files).forEach((file) => {
      if (file.type.startsWith('image/')) {
        const preview = URL.createObjectURL(file);
        newPreviews.push({
          file,
          preview,
          id: Math.random().toString(36).substr(2, 9)
        });
      }
    });
    
    setImagePreviews(prev => [...prev, ...newPreviews]);
  }, []);

  // Remove image preview
  const removeImage = useCallback((id: string) => {
    setImagePreviews(prev => {
      const updated = prev.filter(img => img.id !== id);
      return updated;
    });
  }, []);

  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement> | React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    
    if (text.trim().length === 0) {
      setError('Please enter a product description');
      return;
    }

    if (imagePreviews.length === 0) {
      setError('Please upload at least one image');
      return;
    }

    setLoading(true);
    setError(null);
    setUploadProgress(0);
    setProcessingStep('Starting...');
    
    // Start the cool progress animation
    animateProgress();

    try {
      setUploadProgress(20);

      const formData = new FormData();
      formData.append('text', text);
      formData.append('team_member_token', teamMemberToken);
      formData.append('gps_location', gpsLocation);
      
      imagePreviews.forEach((preview) => {
        formData.append('images', preview.file);
      });

      console.log('Sending request to API', { url: '/api/process_product', method: 'POST', formDataSize: text.length });
      
      const response = await fetch('/api/process_product', {
        method: 'POST',
        body: formData,
      });

      console.log('API response received', { status: response.status, ok: response.ok, headers: response.headers });

      // Read response body once (can only be read once)
      const contentType = response.headers.get('content-type') || '';
      const isJson = contentType.includes('application/json');
      const responseText = await response.text();

      if (!response.ok) {
        // Try to parse as JSON, but handle HTML/text error responses
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          if (isJson) {
            const errorData = JSON.parse(responseText);
            errorMessage = errorData.error || errorMessage;
          } else {
            // If it's not JSON, check for connection errors
            if (responseText.includes('ECONNREFUSED') || responseText.includes('Internal Server Error') || responseText.includes('connect')) {
              // Try to get the API port from environment or default to 5001
              const apiPort = process.env.NEXT_PUBLIC_API_PORT || process.env.API_PORT || '5001';
              errorMessage = `API server is not running. Please start the backend server (python3 api/server.py). Expected port: ${apiPort}`;
            } else {
              errorMessage = `Server error: ${responseText.substring(0, 100)}`;
            }
          }
        } catch (e) {
          // If parsing fails, use default error message
          const apiPort = process.env.NEXT_PUBLIC_API_PORT || process.env.API_PORT || '5001';
          errorMessage = `HTTP error! status: ${response.status}. The API server may not be running on port ${apiPort}.`;
        }
        throw new Error(errorMessage);
      }

      // For successful responses, check if it's JSON
      if (!isJson) {
        throw new Error(`Expected JSON response but got: ${contentType}. Response: ${responseText.substring(0, 200)}`);
      }

      // Parse JSON from the text we already read
      const data = JSON.parse(responseText);
      console.log('API response parsed successfully', { 
        hasDescriptionUrl: !!data.description_url, 
        hasImageUrls: !!data.image_urls, 
        imageUrlCount: data.image_urls?.length || 0,
        teamMember: data.team_member,
        hasZipFile: !!data.zip_file,
        zipFileSize: data.zip_file?.length || 0,
        imagesValidated: data.images_validated,
        imagesFailedValidation: data.images_failed_validation
      });
      
      // Show validation warnings if any images failed
      if (data.images_failed_validation > 0) {
        const warningMsg = `Warning: ${data.images_failed_validation} image(s) failed EXIF validation and were not included. ${data.images_validated} image(s) validated successfully.`;
        console.warn(warningMsg);
        // You could also show this to the user in the UI
      }

      if (data.zip_file) {
        const zipData = atob(data.zip_file);
        const zipArray = new Uint8Array(zipData.length);
        for (let i = 0; i < zipData.length; i++) {
          zipArray[i] = zipData.charCodeAt(i);
        }
        const blob = new Blob([zipArray], { type: 'application/zip' });
        const url = URL.createObjectURL(blob);
        setDownloadUrl(url);
        setProcessingStep('Complete!');
      } else {
        throw new Error('No zip file received from API');
      }

    } catch (err) {
      console.log('Product processing failed', err);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (downloadUrl) {
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `${teamMemberToken}_product.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        // Optional: Revoke the object URL after download to free up memory
        URL.revokeObjectURL(downloadUrl);
        setDownloadUrl(null); // Reset the download button
    }
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: showLoginModal ? '#1F2937' : '#F5F7FA' }}>
      {/* Login Modal */}
      {showLoginModal && (
        <div 
          className="fixed inset-0 flex items-center justify-center z-50"
          style={{ backgroundColor: 'transparent' }}
        >
          <div 
            className="rounded-xl p-8 w-full max-w-md mx-4"
            style={{ 
              backgroundColor: '#FFFFFF',
              boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.3)'
            }}
          >
            <div className="text-center mb-6">
              <img src="/logo.png" alt="Happydeel" className="h-12 w-auto mx-auto mb-4 rounded-lg" />
              <h2 
                className="text-2xl font-semibold mb-2"
                style={{ color: '#1F2937' }}
              >
                {!showPasswordStep ? 'Who are you?' : `Welcome, ${teamMembers.find(m => m.id === selectedMember)?.name}`}
              </h2>
              <p style={{ color: '#6B7280' }}>
                {!showPasswordStep ? 'Select your name to continue' : 'Enter your password to access the dashboard'}
              </p>
            </div>
            
            {!showPasswordStep ? (
              // Step 1: Member Selection
              <div className="space-y-3">
                {teamMembers.map((member) => (
                  <button
                    key={member.id}
                    onClick={() => handleMemberSelect(member.id)}
                    className="w-full py-3 px-4 rounded-lg border transition-all duration-200 ease text-left hover:shadow-md"
                    style={{ 
                      borderColor: '#E8ECEF',
                      backgroundColor: '#FFFFFF',
                      color: '#4B5563',
                      fontSize: '0.875rem',
                      fontWeight: 500
                    }}
                  >
                    {member.name}
                  </button>
                ))}
              </div>
            ) : (
              // Step 2: Password Entry
            <form onSubmit={handleLogin} autoComplete="on">
              {/* Hidden username field for autofill */}
              <input
                type="text"
                name="username"
                value={selectedMember}
                style={{ display: 'none' }}
                autoComplete="username"
                readOnly
              />
              <div className="mb-4">
                <label 
                  className="block text-sm font-medium mb-2"
                  style={{ color: '#4B5563' }}
                  htmlFor="login-password"
                >
                  Password
                </label>
                <input
                  id="login-password"
                  name="password"
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg border transition-colors"
                  style={{ 
                    borderColor: '#E8ECEF',
                    fontSize: '0.875rem',
                    color: '#4B5563'
                  }}
                  placeholder="Enter your password"
                  required
                  autoFocus
                  autoComplete="current-password"
                />
                  {loginError && (
                    <p className="mt-2 text-sm" style={{ color: '#EF4444' }}>
                      {loginError}
                    </p>
                  )}
                </div>
                
                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={handleBackToMembers}
                    className="flex-1 py-3 px-4 rounded-lg border transition-all duration-200 ease"
                    style={{ 
                      borderColor: '#E8ECEF',
                      backgroundColor: '#F9FAFB',
                      color: '#6B7280',
                      fontSize: '0.875rem',
                      fontWeight: 500
                    }}
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    className="flex-1 py-3 text-white rounded-lg font-semibold transition-all duration-200 ease"
                    style={{ 
                      backgroundColor: '#1A9B8E',
                      fontSize: '0.875rem',
                      fontWeight: 500
                    }}
                  >
                    Login
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Main App - Only show when authenticated */}
      {isAuthenticated && (
        <>
          {/* Header */}
          <header className="border-b px-6 py-4" style={{ backgroundColor: '#FFFFFF', borderColor: '#E8ECEF' }}>
            <div className="max-w-7xl mx-auto flex items-center justify-between">
              <div className="flex items-center">
                <img src="/logo.png" alt="Happydeel" className="h-10 w-auto rounded-lg" />
              </div>
              <div className="flex items-center space-x-2" style={{ color: '#6B7280' }}>
                <User size={20} />
                <span className="text-sm font-medium">{teamMemberToken}</span>
                <button
                  onClick={handleLogout}
                  className="ml-2 px-3 py-1 text-xs rounded-md transition-colors"
                  style={{ 
                    backgroundColor: '#F3F4F6',
                    color: '#6B7280'
                  }}
                >
                  Logout
                </button>
              </div>
            </div>
          </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Left Panel - Image Upload */}
          <div className="space-y-6">
            <div 
              className="p-6 transition-all duration-200 ease"
              style={{ 
                backgroundColor: '#FFFFFF', 
                borderRadius: '1rem', 
                boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.08)',
                border: 'none'
              }}
            >
              <h2 
                className="mb-4 flex items-center"
                style={{ 
                  fontSize: '1.25rem', 
                  fontWeight: 600, 
                  color: '#1F2937' 
                }}
              >
                <div 
                  className="mr-3 flex items-center justify-center"
                  style={{ 
                    width: '2.5rem', 
                    height: '2.5rem', 
                    borderRadius: '0.75rem', 
                    backgroundColor: '#F3F4F6' 
                  }}
                >
                  <Upload size={20} style={{ color: '#1A9B8E' }} />
                </div>
                Upload Images
              </h2>
              
              <div 
                className="border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 ease"
                style={{ 
                  borderColor: '#E8ECEF',
                  borderRadius: '0.75rem'
                }}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input 
                  ref={fileInputRef}
                  type="file" 
                  id="fileUpload" 
                  multiple
                  accept="image/webp,image/jpeg,image/png,image/jpg"
                  onChange={(e) => handleFiles(e.target.files)}
                  className="hidden"
                />
                <label htmlFor="fileUpload" className="cursor-pointer">
                  <div 
                    className="mx-auto w-12 h-12 rounded-full flex items-center justify-center mb-4"
                    style={{ backgroundColor: '#FFE8DC' }}
                  >
                    <Upload size={24} style={{ color: '#1A9B8E' }} />
                  </div>
                  <p className="mb-2" style={{ color: '#4B5563', fontSize: '1rem' }}>Click to upload or drag and drop</p>
                  <p className="text-sm" style={{ color: '#9CA3AF' }}>PNG, JPG, WEBP up to 10MB each</p>
                </label>
              </div>

              {/* Image Previews */}
              {imagePreviews.length > 0 && (
                <div className="mt-6">
                  <h3 
                    className="mb-3"
                    style={{ 
                      fontSize: '0.875rem', 
                      fontWeight: 500, 
                      color: '#6B7280' 
                    }}
                  >
                    Selected Images ({imagePreviews.length})
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    {imagePreviews.map((preview) => (
                      <div key={preview.id} className="relative group">
                        <img 
                          src={preview.preview} 
                          alt="Preview" 
                          className="w-full h-24 object-cover rounded-lg"
                          style={{ border: '1px solid #E8ECEF' }}
                        />
                        <button 
                          type="button"
                          onClick={() => removeImage(preview.id)}
                          className="absolute -top-2 -right-2 w-6 h-6 text-white rounded-full flex items-center justify-center text-xs transition-colors"
                          style={{ backgroundColor: '#EF4444' }}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Country Selection */}
            <div 
              className="p-6 transition-all duration-200 ease"
              style={{ 
                backgroundColor: '#FFFFFF', 
                borderRadius: '1rem', 
                boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.08)',
                border: 'none'
              }}
            >
              <h3 
                className="mb-4 flex items-center"
                style={{ 
                  fontSize: '1.25rem', 
                  fontWeight: 600, 
                  color: '#1F2937' 
                }}
              >
                <div 
                  className="mr-3 flex items-center justify-center"
                  style={{ 
                    width: '2.5rem', 
                    height: '2.5rem', 
                    borderRadius: '0.75rem', 
                    backgroundColor: '#F3F4F6' 
                  }}
                >
                  <MapPin size={20} style={{ color: '#1A9B8E' }} />
                </div>
                GPS Location
              </h3>
              <select 
                className="w-full px-4 py-3 rounded-lg transition-colors"
                style={{ 
                  border: '1px solid #E8ECEF',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  color: '#4B5563'
                }}
                value={gpsLocation}
                onChange={(e) => setGpsLocation(e.target.value)}
              >
                <option value="usa">Choose Country</option>
                <option value="usa">United States</option>
                <option value="canada">Canada</option>
                <option value="germany">Germany</option>
                <option value="australia">Australia</option>
                <option value="france">France</option>
              </select>
            </div>
          </div>

          {/* Right Panel - Description */}
          <div className="space-y-6">
            <div 
              className="p-6 h-full transition-all duration-200 ease"
              style={{ 
                backgroundColor: '#FFFFFF', 
                borderRadius: '1rem', 
                boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.08)',
                border: 'none'
              }}
            >
              <h2 
                className="mb-4 flex items-center"
                style={{ 
                  fontSize: '1.25rem', 
                  fontWeight: 600, 
                  color: '#1F2937' 
                }}
              >
                <div 
                  className="mr-3 flex items-center justify-center"
                  style={{ 
                    width: '2.5rem', 
                    height: '2.5rem', 
                    borderRadius: '0.75rem', 
                    backgroundColor: '#F3F4F6' 
                  }}
                >
                  <FileText size={20} style={{ color: '#1A9B8E' }} />
                </div>
                Product Description
              </h2>
              <textarea 
                className="w-full h-64 px-4 py-3 rounded-lg resize-none transition-colors"
                style={{ 
                  border: '1px solid #E8ECEF',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  color: '#4B5563'
                }}
                placeholder="Enter your product description here..."
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex flex-col items-center space-y-6">
          <button 
            className="px-8 py-4 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 ease flex items-center space-x-2"
            style={{ 
              backgroundColor: '#1A9B8E',
              borderRadius: '0.5rem',
              fontSize: '0.875rem',
              fontWeight: 500
            }}
            disabled={loading || !text.trim() || imagePreviews.length === 0}
            onClick={handleSubmit}
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Zap size={20} />
                <span>Start Processing</span>
              </>
            )}
          </button>

          {/* Progress Bar */}
          {loading && (
            <div className="w-full max-w-md space-y-4">
              <div 
                className="rounded-full h-2 overflow-hidden"
                style={{ backgroundColor: '#E8ECEF' }}
              >
                <div 
                  className="h-full transition-all duration-500 ease-out"
                  style={{ 
                    width: `${uploadProgress}%`,
                    background: 'linear-gradient(135deg, #1A9B8E 0%, #2DB5A6 100%)'
                  }}
                />
              </div>
              <div className="flex justify-center space-x-4">
                {progressDots.map((isActive, index) => (
                  <div 
                    key={index}
                    className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                      isActive ? 'scale-110' : ''
                    }`}
                    style={{
                      backgroundColor: isActive ? '#1A9B8E' : '#E8ECEF',
                      color: isActive ? '#FFFFFF' : '#9CA3AF'
                    }}
                  >
                    {isActive && <CheckCircle size={16} />}
                  </div>
                ))}
              </div>
              {processingStep && (
                <p 
                  className="text-center text-sm"
                  style={{ color: '#6B7280' }}
                >
                  {processingStep}
                </p>
              )}
            </div>
          )}

          {downloadUrl && (
            <button 
              className="px-8 py-4 text-white rounded-lg font-semibold transition-all duration-200 ease flex items-center space-x-2"
              style={{ 
                backgroundColor: '#10B981',
                borderRadius: '0.5rem',
                fontSize: '0.875rem',
                fontWeight: 500
              }}
              onClick={handleDownload}
            >
              <Download size={20} />
              <span>Download Results</span>
            </button>
          )}
        </div>

        {/* Messages */}
        {error && (
          <div 
            className="mt-6 rounded-lg p-4"
            style={{ 
              backgroundColor: '#FEE2E2',
              border: '1px solid #FECACA'
            }}
          >
            <div className="flex items-center">
              <div className="mr-3" style={{ color: '#EF4444' }}>⚠️</div>
              <p style={{ color: '#991B1B' }}>{error}</p>
            </div>
          </div>
        )}

        {downloadUrl && (
          <div 
            className="mt-6 rounded-lg p-4"
            style={{ 
              backgroundColor: '#D1FAE5',
              border: '1px solid #A7F3D0'
            }}
          >
            <div className="flex items-center">
              <div className="mr-3" style={{ color: '#10B981' }}>✅</div>
              <p style={{ color: '#065F46' }}>Processing complete! Your files are ready for download.</p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 py-6 border-t border-gray-200">
        <div className="text-center">
          <p className="text-sm text-gray-600">
            Developed with love by{' '}
            <span className="font-semibold text-gray-800">Mehdi(L3alawi)</span>
          </p>
        </div>
      </footer>
        </>
      )}
    </div>
  );
}