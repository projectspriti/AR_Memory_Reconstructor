import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Processing = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const navigate = useNavigate();

  const steps = [
    { name: 'Analyzing Image', description: 'AI is examining your photograph for depth and structure' },
    { name: 'Depth Reconstruction', description: 'Creating depth maps and spatial understanding' },
    { name: 'Scene Generation', description: 'Building the 3D environment from your memory' },
    { name: 'Lighting Optimization', description: 'Enhancing lighting and atmospheric effects' },
    { name: 'AR Preparation', description: 'Preparing your scene for augmented reality viewing' }
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => navigate('/ar-viewer'), 1000);
          return 100;
        }
        return prev + 2;
      });
    }, 200);

    return () => clearInterval(interval);
  }, [navigate]);

  useEffect(() => {
    const stepIndex = Math.floor(progress / 20);
    setCurrentStep(Math.min(stepIndex, steps.length - 1));
  }, [progress, steps.length]);

  return (
    <div className="max-w-2xl mx-auto animate-fade-in">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-4">Reconstructing Your Memory</h1>
        <p className="text-gray-600">
          Our AI is working to transform your photograph into an immersive 3D experience
        </p>
      </div>

      <div className="bg-white rounded-2xl shadow-lg p-8">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-blue-600 to-purple-600 h-3 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        {/* Current Step */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <div className="w-8 h-8 border-2 border-white rounded-full animate-spin border-t-transparent"></div>
          </div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            {steps[currentStep]?.name}
          </h2>
          <p className="text-gray-600">
            {steps[currentStep]?.description}
          </p>
        </div>

        {/* Steps List */}
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div
              key={index}
              className={`flex items-center p-3 rounded-lg transition-all ${
                index < currentStep
                  ? 'bg-green-50 border border-green-200'
                  : index === currentStep
                  ? 'bg-blue-50 border border-blue-200'
                  : 'bg-gray-50 border border-gray-200'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 ${
                  index < currentStep
                    ? 'bg-green-500 text-white'
                    : index === currentStep
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-300 text-gray-600'
                }`}
              >
                {index < currentStep ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <span className="text-sm font-medium">{index + 1}</span>
                )}
              </div>
              <div>
                <h3 className="font-medium text-gray-800">{step.name}</h3>
                <p className="text-sm text-gray-600">{step.description}</p>
              </div>
            </div>
          ))}
        </div>

        {progress === 100 && (
          <div className="mt-8 text-center">
            <div className="inline-flex items-center px-4 py-2 bg-green-100 text-green-800 rounded-full">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Reconstruction Complete!
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Processing;