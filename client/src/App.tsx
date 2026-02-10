import React from 'react';
import { ChakraProvider, Box } from '@chakra-ui/react';
import { BrowserRouter, Routes, Route, useParams } from 'react-router-dom';
import HomePage from './pages/HomePage';
import SubjectPage from './pages/SubjectPage';
import TextbookPage from './pages/TextbookPage';
import { getSubjectConfig } from './config/subjects';
import './App.css';

// Wrapper component to extract subject from URL params
const SubjectPageWrapper: React.FC = () => {
  const { subject } = useParams<{ subject: string }>();
  
  if (!subject) {
    return <div>Subject not specified</div>;
  }

  try {
    // Validate subject exists
    getSubjectConfig(subject);
    return <SubjectPage subjectId={subject} />;
  } catch (error) {
    return <div>Subject not found: {subject}</div>;
  }
};

const TextbookPageWrapper: React.FC = () => {
  const { subject } = useParams<{ subject: string }>();
  
  if (!subject) {
    return <div>Subject not specified</div>;
  }

  try {
    // Validate subject exists
    getSubjectConfig(subject);
    return <TextbookPage subject={subject} />;
  } catch (error) {
    return <div>Subject not found: {subject}</div>;
  }
};

function App() {
  return (
    <ChakraProvider>
      <BrowserRouter>
        <Box minH="100vh" bg="gray.50">
          <Routes>
            <Route path="/" element={<HomePage />} />
            
            {/* Dynamic subject routes */}
            <Route path="/subject/:subject" element={<SubjectPageWrapper />} />
            <Route path="/textbook/:subject" element={<TextbookPageWrapper />} />
            <Route path="/textbook/:subject/unit/:unitId" element={<TextbookPageWrapper />} />
            <Route path="/textbook/:subject/unit/:unitId/chapter/:chapterId" element={<TextbookPageWrapper />} />
            
            {/* Catch-all for unknown routes */}
            <Route path="*" element={<div>Page not found</div>} />
          </Routes>
        </Box>
      </BrowserRouter>
    </ChakraProvider>
  );
}

export default App;
