import React from 'react';
import { ChakraProvider, Box } from '@chakra-ui/react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import MicroEconomicsPage from './pages/MicroEconomicsPage';
import MacroEconomicsPage from './pages/MacroEconomicsPage';
import TextbookPage from './pages/TextbookPage';
import './App.css';

function App() {
  return (
    <ChakraProvider>
      <BrowserRouter>
        <Box minH="100vh" bg="gray.50">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/micro" element={<MicroEconomicsPage />} />
            <Route path="/macro" element={<MacroEconomicsPage />} />
            <Route path="/textbook/micro" element={<TextbookPage subject="micro" />} />
            <Route path="/textbook/micro/unit/:unitId" element={<TextbookPage subject="micro" />} />
            <Route path="/textbook/micro/unit/:unitId/chapter/:chapterId" element={<TextbookPage subject="micro" />} />
            <Route path="/textbook/macro" element={<TextbookPage subject="macro" />} />
            <Route path="/textbook/macro/unit/:unitId" element={<TextbookPage subject="macro" />} />
            <Route path="/textbook/macro/unit/:unitId/chapter/:chapterId" element={<TextbookPage subject="macro" />} />
          </Routes>
        </Box>
      </BrowserRouter>
    </ChakraProvider>
  );
}

export default App;
