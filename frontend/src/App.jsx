import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import MapContainer from './components/MapContainer';
import ImpactDashboard from './components/ImpactDashboard';

const API_PORT = import.meta.env.VITE_API_PORT || '8000';
const API_BASE_URL = `http://localhost:${API_PORT}`;

function App() {
  const [locations, setLocations] = useState([]);
  const [selectedSuburb, setSelectedSuburb] = useState('');
  const [selectedStreet, setSelectedStreet] = useState('');
  const [blocksGeoJson, setBlocksGeoJson] = useState(null);
  const [selectedBlock, setSelectedBlock] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch supported locations on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/locations`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && data.suburbs.length > 0) {
          setLocations(data.suburbs);
          
          // Default to Melbourne (CBD) and La Trobe Street if available
          const cbd = data.suburbs.find(s => s.name === 'Melbourne (CBD)');
          if (cbd && cbd.streets.includes('La Trobe Street')) {
            setSelectedSuburb('Melbourne (CBD)');
            setSelectedStreet('La Trobe Street');
          } else {
            setSelectedSuburb(data.suburbs[0].name);
            setSelectedStreet(data.suburbs[0].streets[0]);
          }
        }
      })
      .catch(err => console.error('Error fetching locations:', err));
  }, []);

  // Update selected street when suburb changes
  const handleSuburbChange = (suburb) => {
    setSelectedSuburb(suburb);
    setSelectedStreet('All Streets');
  };

  // Fetch blocks when street or suburb changes
  useEffect(() => {
    if (!selectedSuburb) return;
    
    setLoading(true);
    setBlocksGeoJson(null);
    setSelectedBlock(null);
    
    let url = `${API_BASE_URL}/api/blocks?suburb=${encodeURIComponent(selectedSuburb)}`;
    if (selectedStreet && selectedStreet !== 'All Streets') {
      url += `&street=${encodeURIComponent(selectedStreet)}`;
    }
    
    fetch(url)
      .then(res => res.json())
      .then(data => {
        if (data.type === 'FeatureCollection') {
          setBlocksGeoJson(data);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching blocks:', err);
        setLoading(false);
      });
  }, [selectedSuburb, selectedStreet]);

  // Update document title dynamically
  useEffect(() => {
    if (selectedSuburb) {
      const streetLabel = selectedStreet && selectedStreet !== 'All Streets' ? selectedStreet : selectedSuburb;
      document.title = `${streetLabel} Bike Lanes | Urban Impact Dashboard`;
    } else {
      document.title = 'Urban Mobility Impact Dashboard';
    }
  }, [selectedSuburb, selectedStreet]);

  const handleBlockClick = (blockDesc) => {
    setSelectedBlock(blockDesc);
  };

  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', position: 'relative' }}>
      <Header 
        suburbs={locations}
        selectedSuburb={selectedSuburb}
        selectedStreet={selectedStreet}
        onSuburbChange={handleSuburbChange}
        onStreetChange={setSelectedStreet}
      />
      
      <MapContainer 
        blocksGeoJson={blocksGeoJson}
        loading={loading}
        onBlockClick={handleBlockClick}
        selectedBlock={selectedBlock}
        selectedStreet={selectedStreet}
        selectedSuburb={selectedSuburb}
      />
      
      <ImpactDashboard 
        suburb={selectedSuburb}
        street={selectedStreet}
        selectedBlock={selectedBlock}
        onBlockClick={handleBlockClick}
        blocksGeoJson={blocksGeoJson}
      />
    </div>
  );
}

export default App;
